#!/usr/bin/env - python
from couchbase.bucket import Bucket
import couchbase.subdocument as SD
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


while True:
    print "."
    results = SDK_CLIENT.n1ql_query(
    'SELECT symbol,price FROM {} WHERE symbol IS NOT MISSING AND price IS NOT MISSING'.format(bucket_name, ))
    for row in results:
        stock_key = "stock:"+ (row['symbol'])
        new_price = round ( (float(row['price']) * 1.5) ,2)
        SDK_CLIENT.mutate_in(stock_key,
                            SD.upsert('price', new_price))

