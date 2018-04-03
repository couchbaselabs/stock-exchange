#!/usr/bin/env - python
from __future__ import print_function

from couchbase.bucket import Bucket
import settings
import random
import csv

bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD
if settings.AWS:
    node = settings.AWS_NODES[0]
else:
    node = settings.AZURE_NODES[0]

SDK_CLIENT = Bucket('couchbase://{0}/{1}'.format(node, bucket_name),
                    username=user, password=password)

SDK_CLIENT.timeout = 15

def check_and_create_view():
    design_doc = {
        'views': {
            'by_timestamp': {
                'map': '''
                function(doc, meta) {
                    if (doc.type && doc.type== "order" && doc.ts) {
                        emit(doc.ts, null)
                    }
                    }
                '''
                }
            }
        }

    mgr = SDK_CLIENT.bucket_manager()
    mgr.design_create(settings.DDOC_NAME, design_doc, use_devmode=False)
    res = SDK_CLIENT.query(settings.DDOC_NAME, settings.VIEW_NAME)
    for row in res:
        print (row)


def add_stocks():
    # https://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download
    stocks_csv = open(settings.STOCKS_FILE,'r')
    stocks_dict = csv.DictReader(stocks_csv)
    symbol_list = []
    stock_count = 0
    for entry in stocks_dict:
        if stock_count >= settings.NUM_STOCKS:
            break
        stock_doc = { 'symbol': entry['Symbol'],
                      'price' : entry['LastSale'],
                      'sector':  entry['Sector'],
                      'company': entry['Name']
                    }
        stock_key = "stock:" + stock_doc['symbol']
        if stock_doc['price'] =="n/a":
            stock_doc['price'] = 9.99
        stock_doc['price'] = round (float(stock_doc['price']),2)
        stock_doc['starting_price'] = stock_doc['price']
        symbol_list.append(stock_key)
        SDK_CLIENT.upsert(stock_key, stock_doc)
        stock_count += 1
    SDK_CLIENT.upsert(settings.PRODUCT_LIST, {"symbols": symbol_list})



if __name__ == '__main__':
    add_stocks()
    check_and_create_view()
    print("Successfully populated dataset")
