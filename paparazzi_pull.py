from bs4 import BeautifulSoup
import requests
import re
import datetime
import urlparse

import os
import django

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

DAYS_BACK = 1

FROM_EMAIL = 'ultimat3high@gmail.com'
FROM_PASSWORD = 'mingyboy'
#TO_EMAIL = ['crvillaluz@gmail.com', 'lorencdavid@gmail.com']
TO_EMAIL = ['crvillaluz@gmail.com', 'lorencdavid@gmail.com']
new_items = []

os.environ["DJANGO_SETTINGS_MODULE"] = 'paparazzi_django.settings'
django.setup()
from paparazzi.models import Item

def main():
    url = "https://paparazziaccessories.com/shop/"
    pages = get_pages(url)
    all_items = get_all_items(url, pages)
    new_items = get_new_items(all_items)
    html = get_html(new_items)
    if html:
        send_email(html)
        
    reset_being_sold()
    store_items(all_items)

    date = datetime.datetime.now()
    print 'ran at %s' % date

def get_all_items(url, pages, start_page=1):
    all_items = []
    for p in range(start_page, pages):
        new_url = '%s?page=%s' % (url, p)
        items = get_items(url, new_url)
        all_items.extend(items)
    return all_items

def get_pages(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    p = re.compile('var page_last = (.*);')  
    for script in soup.find_all("script", {"src":False}):
        if script:            
            m = p.search(script.string)
            if m:
                return int(m.group(1))

def get_items(og_url, url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.find_all("div", "js-product-box")
    items = []
    for div in divs:
        ahref = div.find('a')
        link = ahref['href']
        link = urlparse.urljoin(og_url, link)
        img = div.find("img")
        title_original = img['title']
        split = title_original.split(" - ")
        title = split[0]
        color = None if len(split) == 1 else split[1]
        today = datetime.datetime.today()
        item = {
            "title_original": title_original,
            "image_url": img['src'],
            "title": title,
            "color": color,
            "date_created": today,
            "url": link,
            "being_sold": True,
            "date_found_sold": today
        }
        items.append(item)
        #print item
    return items

def reset_being_sold():
    Item.objects.update(being_sold=False)

def get_new_items(items):
    #first get all the items that were previously being sold
    inner_qs = Item.objects.filter(being_sold=True).values_list('id', flat=True)
    db_titles = list(Item.objects.filter(id__in=inner_qs).values_list('title_original', flat=True))
    
    #get the titles of the current items that are being sold
    pap_titles = get_titles_from_items(items)
   
    #get the difference of the current and old items
    new_titles = list(set(pap_titles) - set(db_titles))
    new_items = [item for item in items if item.get('title_original') in new_titles]

    #if old item being sold again, get only within the date set
    past = datetime.datetime.today() - datetime.timedelta(days=DAYS_BACK)
    inner_qs = Item.objects.filter(date_found_sold__gte=past).values_list('id', flat=True)
    db_titles = list(Item.objects.filter(id__in=inner_qs).values_list('title_original', flat=True))
    new_items = [item for item in items if item.get('title_original') not in db_titles]
    return new_items

def get_titles_from_items(items):
    return [item.get('title_original') for item in items]

def store_items(items):
    for item in items:
        # item_obj, created = Item.objects.update_or_create(
        #     title_original=item.get('title_original'), defaults=item
        # )
        title_original = item.get('title_original')
        item_obj, created = Item.objects.get_or_create(
            title_original=title_original, defaults=item
        )
        if not created:
            del item['date_created']
            Item.objects.filter(title_original=title_original).update(**item)
        # print created
        #title_original is the "unique key" where we want to update by
        #defaults parameter is the values that we want to update if a row already exists
        
def send_email(msg):
    date = datetime.datetime.now().date()

    message = MIMEMultipart("alternative")
    message['From'] = FROM_EMAIL
    message['To'] = ",".join(TO_EMAIL)
    message['Subject'] = 'Paparazzi: New Arrivals %s' % date

    the_msg = MIMEText(msg, 'html')
    message.attach(the_msg)

    try:
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.login(FROM_EMAIL, FROM_PASSWORD)
        text = message.as_string()
        smtp_server.sendmail(FROM_EMAIL, TO_EMAIL, text)
        print 'sent email'
        smtp_server.quit()
    except smtplib.SMTPException:
        print 'failed to send email'
        smtp_server.quit()

def get_html(new_items):
    html = ''
    for item in new_items:
        url = item.get('url')
        print item.get('title_original'), url
        image_url = item.get('image_url')
        html += '<div><a href="%s"><img src="%s" style="width: 40%%; height:auto"></img></a></div>' % (url, image_url)
    return html

if __name__ == '__main__':
    main()