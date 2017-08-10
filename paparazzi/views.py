# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connection
from models import Item, Stock
from util.datatablesdf import DataTablesDF
import json
import pandas as pd
import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

ROW_SIZE = 3
PER_PAGE = ROW_SIZE * 3

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]

def drop_df_columns(columns, df, not_in=False):
    if not_in:
        cols = list(df.columns.values)
        columns = list(set(cols) - set(columns))
    for column in columns:
        df = df.drop(column, axis=1)
    df = df.loc[:,~df.columns.duplicated()] #drop duplicate column
    return df

def index(request, page=1):
    page = int(page)
    start = (page-1) * 10
    end = start+PER_PAGE
    #items = Item.objects.all()[start:end]
    items = [stock.item for stock in Stock.objects.select_related()][start:end]
    items = list(chunks(items, ROW_SIZE))
    context = {
        'items': items,
        'request_url': request.path,
        'page': page
    }
    if not items:
        context['page'] = -1
    return render(request, 'index.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin(request):
    columns_order = ['id', 'image_url', 'title_original', 'title', 'color', 'being_sold']
    columns = [{'data': col} for col in columns_order]
    context = {
        'columns': json.dumps(columns),
        'table_header': columns_order
    }
    return render(request, 'admin_panel.html', context)

def get_admin_items(request):
    response_data = json.dumps(request.GET.dict())
    print response_data
    columns_order = ['id', 'image_url', 'title_original', 'title', 'color', 'being_sold', 'url']
    inner_qs = Stock.objects.values_list('item_id',flat=True)
    query = str(Item.objects.exclude(id__in=inner_qs).only(*columns_order).query)
    df = pd.read_sql_query(query, connection)
    results = DataTablesDF(df, response_data, columns_order)
    results = results.output_result()

    return HttpResponse(results, content_type='application/json')

def get_stock_items(request):
    response_data = json.dumps(request.GET.dict())
    print response_data
    columns_order = ['id', 'image_url', 'title_original', 'title', 'color', 'being_sold', 'quantity']
    query = str(Stock.objects.select_related().query) #pass in a query that has the all columns with the join
    df = pd.read_sql_query(query, connection)
    df = drop_df_columns(columns_order, df, not_in=True) #remove all the columns we dont care about in the df
    results = DataTablesDF(df, response_data, columns_order)
    results = results.output_result()

    return HttpResponse(results, content_type='application/json')

def sell_item(request):
    stock = request.POST.dict()
    is_add = stock.get('is_add')
    if is_add:
        stock['date_created'] = datetime.datetime.today()
    del stock['csrfmiddlewaretoken']
    del stock['is_add']
    stock_obj, created = Stock.objects.update_or_create(
        item_id=stock.get('id'), defaults=stock
    )
    return JsonResponse({'success': True})

def delete_item(request):
    stock = request.POST.dict()
    stock_obj = Stock.objects.get(item_id=stock.get('id'))
    stock_obj.delete()
    return JsonResponse({'success': True})