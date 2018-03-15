#!/usr/bin/env - python
from couchbase.bucket import Bucket
import settings


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

symbol_list =     SDK_CLIENT.get(settings.PRODUCT_LIST).value

for entry in symbol_list['symbols']:
    print (entry)
    stock_doc = SDK_CLIENT.get(entry).value
    stock_doc['price'] = float(stock_doc['price']) * 2
    SDK_CLIENT.upsert(entry, stock_doc)
