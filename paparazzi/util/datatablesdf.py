import json
from datetime import datetime
import numpy as np
import functools

def conjunction_or(*conditions):
    return functools.reduce(np.logical_or, conditions)

def is_number(n):
    try:
        float(n)
        return True
    except ValueError:
        return False

def strbool_to_bool(s):
    trues = ['true', 't', 'True', 'T']
    falses = ['false', 'f', 'False', 'F']
    if any(s == valid for valid in trues):
        return True
    elif any(s == valid for valid in falses):
        return False
    return None

class DataTablesDF(object):
    def __init__(self, dataframe, json_request, datatables_columns, sticky_sort=[], total_records=None):
        """
        dataframe: pandas dataframe
        json_request: json formed request
        datatables_columns: the columns for the dataframe
        sticky_sort: a list of a list that holds the column name and True if asc else False for desc
        total_records: total count of all the records, optional
        """
        self.df = dataframe
        self.request = json.loads(json_request)
        self.columns = datatables_columns
        self.sticky_sort = sticky_sort

        try:
            self.df = self.df.drop('_sa_instance_state', 1)
        except Exception as e:
            #print e
            pass
            
        self.df = self.df[datatables_columns]

        self.total_records = total_records if total_records else len(self.df.index)
        self.filtered_records = self.total_records
        self.results = []

        # print self.request

    def run(self):
        self.sort()
        self.filter()
        self.page()

    def format_results(self):
        for row in self.df.values:
            new_row = {}
            for idx, cell in enumerate(row):
                if type(cell) is unicode:
                    cell = cell.encode('utf8')
                elif type(cell) is float:
                    cell = str(cell)
                    if cell[::-1].find('.') == 1:
                        cell = cell.split('.')[0]
                    if cell == 'nan':
                        cell = ''
                elif cell:
                    cell = str(cell)
                else:
                    cell = ''
                #new_row.update({str(idx):cell})
                new_row.update({self.columns[idx]:cell})
            self.results.append(new_row)

    def get_filtered_df(self):
        self.sort()
        self.filter()
        return self.df

    def to_csv(self):
        self.sort()
        self.filter()
        csv = self.df.to_csv(encoding='utf-8', index=False)
        return csv

    def output_result(self):
        self.run()
        self.format_results()

        output = {}
        output['draw'] = int(self.request['draw'])
        output['recordsTotal'] = str(self.total_records)
        output['recordsFiltered'] = str(self.filtered_records)
        output['data'] = self.results
        return json.dumps(output)

    def sort(self):
        request = self.request
        columns = self.columns
        sort_columns, sort_directions = [], []
        if self.sticky_sort:
            for sort in self.sticky_sort:
                column, direction = sort
                sort_columns.append(column)
                sort_directions.append(direction)

        #find the ordered columns first
        for idx, col in enumerate(columns):
            orderable = "columns[%s][orderable]" % idx
            is_orderable = strbool_to_bool(request[orderable])
            # if is_orderable:
            order_dir = "order[%s][dir]" % idx
            #find the columns that are ordered.
            direction = request.get(order_dir)
            direction = True if direction == 'asc' else False
            col_check = "order[%s][column]" % idx
            value = request.get(col_check)
            if value:
                value = int(value)
                sort_column = columns[value]
                sort_columns.append(sort_column)
                sort_directions.append(direction)
        self.df = self.df.sort_values(by=sort_columns, ascending=sort_directions)
        return self.df

    def page(self):
        request = self.request
        start = int(request['start'])
        length = int(request['length'])
        end = start + length
        self.df = self.df[start:end]
        return self.df

    def filter(self):
        columns = self.columns
        request = self.request
        filtered = False
        global_search = request.get("search[value]")
        if global_search:
            #better way to do this?
            lst = []
            for col in self.df:
                col_type = self.df[col].dtype
                if not (col_type == np.int64 or col_type == np.float64):
                    s = self.df[col].str.contains("%s" % global_search, na=False, case=False)
                    lst.append(s)
            self.df = self.df[conjunction_or(*lst)]
            self.filtered_records = len(self.df.index)
        else:
            for idx, column in enumerate(columns):
                search_value = request.get('columns[%s][search][value]' % idx, None)
                # print column, search_value == ''

                if search_value:
                    filtered = True
                    #print column, 'sSearch_adv_%d' % idx, search_value
                    if search_value == '^unfilled$':
                        self.df = self.df[( self.df[column].isnull() ) | ( self.df[column] == '' )]
                    elif '~' in search_value: #range filter
                        index = search_value.index('~')
                        first_number = search_value[0:index]
                        second_number = search_value[index+1:len(search_value)+1]
                        print first_number, second_number
                        if is_number(first_number) or is_number(second_number): #if its a number
                            first_number = float('-inf') if first_number == "" else float(first_number)
                            second_number = float('inf') if second_number == "" else float(second_number)
                        else: #a date
                            first_number = datetime.min.date() if first_number == "" else datetime.strptime(first_number, '%Y-%m-%d').date()
                            second_number = datetime.max.date() if second_number == "" else datetime.strptime(second_number, '%Y-%m-%d').date()
                        self.df = self.df[(self.df[column] >= first_number) & (self.df[column] <= second_number)]
                    else:
                        self.df = self.df[self.df[column].str.contains(search_value, case=False, na=False)]

            self.filtered_records = len(self.df.index) if filtered else self.total_records
        return self.df
