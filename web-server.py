#!/usr/bin/env python
from collections import deque
import datetime
import random
import time
import urllib

import tornado.gen
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.platform.twisted
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

#install this before importing anything else, or VERY BAD THINGS happen
tornado.platform.twisted.install()

from txcouchbase.bucket import Bucket

import cb_status
import settings


socket_list = []
bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD

if settings.AWS:
    node = settings.AWS_NODES[0]
else:
    node = settings.AZURE_NODES[0]

bucket = Bucket('couchbase://{0}/{1}'.format(node, bucket_name),
                username=user, password=password)
fts_nodes = None
fts_enabled = False
nodes = []
n1ql_enabled = False
xdcr_enabled = False
price_data = {}
portfolio_cache = []

class ExchangeHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        company_list = yield bucket.get(settings.PRODUCT_LIST)
        stocks = yield bucket.get_multi(company_list.value['symbols'])
        self.render("www/exchange.html", stocks=stocks)

class LatestOrdersHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("www/orders.html")

class StockLeaderboardHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("www/stock_performance.html")

class InvestorLeaderboardHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("www/investor_performance.html")

class ClusterVisHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("www/visualiser.html")

class CBStatusWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.NAME = "CB Status"
        if self not in socket_list:
            socket_list.append(self)
            self.red = 255
            print("{} WebSocket opened").format(self.NAME)
            self.callback = tornado.ioloop.PeriodicCallback(
                self.get_node_status, 1000)
            self.callback.start()
            self.get_node_status()

    def on_message(self, message):
        print "{} received: {}".format(self.NAME, message)

    def on_close(self):
        print("{} WebSocket closed").format(self.NAME)
        self.callback.stop()

    def get_node_status(self):
        msg = {"nodes": nodes, 'fts': fts_enabled,
               'n1ql': n1ql_enabled, 'xdcr': xdcr_enabled}
        self.write_message(msg)


class LiveOrdersWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.RECENT_ORDERS = deque(maxlen=50)
        self.NEXT_CUSTOMER = 0
        self.PORTFOLIO_INDEX = 0
        self.NAME = "Live Orders"
        if self not in socket_list:
            socket_list.append(self)
            print("{} WebSocket opened").format(self.NAME)
            self.callback = tornado.ioloop.PeriodicCallback(self.send_orders,
                                                            5000)
            self.callback.start()

    def on_message(self, message):
        print "{} received: {}".format(self.NAME, message)

    def on_close(self):
        print("{} WebSocket closed").format(self.NAME)
        self.callback.stop()

    @tornado.gen.coroutine
    def send_orders(self):

        if len(portfolio_cache) > self.PORTFOLIO_INDEX:
            self.RECENT_ORDERS.extendleft(portfolio_cache[self.PORTFOLIO_INDEX:])
            self.PORTFOLIO_INDEX = len(portfolio_cache)

        if len(self.RECENT_ORDERS) > 0:
            display_order = self.RECENT_ORDERS.pop()
            msg = {"name": display_order['name'], "order": display_order['order']}
            self.write_message(msg)
            if display_order['name'] == 'Couchbase Demo Phone' and self.NEXT_CUSTOMER == 0:
                self.callback.stop()
                yield tornado.gen.sleep(5)
                self.callback.start()

class StockLeaderboardWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.NAME = "Stock Leaderboard"
        if self not in socket_list:
            socket_list.append(self)
            print("{} WebSocket opened").format(self.NAME)
            self.callback = tornado.ioloop.PeriodicCallback(self.send_leaderboard,
                                                            5000)
            self.callback.start()

    def on_message(self, message):
        print "{} received: {}".format(self.NAME, message)

    def on_close(self):
        print("{} WebSocket closed").format(self.NAME)
        self.callback.stop()

    @tornado.gen.coroutine
    def send_leaderboard(self):
        base_query = 'SELECT price_diff,symbol,starting_price,price from {} \
         LET price_diff = 100 * ((price - starting_price))/starting_price \
         WHERE starting_price is not MISSING \
         ORDER BY price_diff {} \
         LIMIT 10'
        best_results = yield bucket.n1qlQueryAll(base_query.format(bucket_name, "DESC"))
        good_performers = []
        for row in best_results:
            good_performers.append(row)
        worst_results = yield bucket.n1qlQueryAll(base_query.format(bucket_name, ""))
        poor_performers = []
        for row in worst_results:
            poor_performers.append(row)
        self.write_message({"best": good_performers, "worst": poor_performers})



class InvestorLeaderboardWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.NAME = "Investor Leaderboard"
        if self not in socket_list:
            socket_list.append(self)
            print("{} WebSocket opened").format(self.NAME)
            self.callback = tornado.ioloop.PeriodicCallback(self.send_leaderboard,
                                                            5000)
            self.callback.start()

    def on_message(self, message):
        print "{} received: {}".format(self.NAME, message)

    def on_close(self):
        print("{} WebSocket closed").format(self.NAME)
        self.callback.stop()

    @tornado.gen.coroutine
    def send_leaderboard(self):
        global portfolio_cache
        list_to_sort = [(portfolio["current_value"], portfolio) for portfolio in portfolio_cache]
        list_to_sort.sort(reverse=True)
        sorted_portfolios = [portfolio for (key, portfolio) in list_to_sort]
        best_performers = sorted_portfolios[:5]
        worst_performers = sorted_portfolios[-5:]
        self.write_message({"best": best_performers, "worst": worst_performers})



class LivePricesWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.NAME = "Live Prices"
        if self not in socket_list:
            socket_list.append(self)
            print("{} WebSocket opened").format(self.NAME)
            self.callback = tornado.ioloop.PeriodicCallback(self.send_prices,
                                                            5000)
            self.callback.start()

    def on_message(self, message):
        print "{} received: {}".format(self.NAME, message)

    def on_close(self):
        print("{} WebSocket closed").format(self.NAME)
        self.callback.stop()

    @tornado.gen.coroutine
    def send_prices(self):
        self.write_message(price_data)


class SubmitHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)

        # Someone has sent us an invalid order, send a 400
        if 'name' not in data or 'order' not in data or \
                ('order' in data and len(data['order']) != 5):
            self.send_error(400)
            return

        key = "Order::{}::{}".format(data['name'],
                                     datetime.datetime.utcnow().isoformat())
        data['ts'] = int(time.time())
        data['type'] = "order"
        order = []
        for i in range (0,5):
            stock = data['order'][i];
            purchase_price = float(price_data[stock[6:]])
            quantity = 100.0 / purchase_price
            d = {'symbol': stock[6:], 'purchase_price': purchase_price, 'quantity': quantity }
            order.append(d)
        data['order'] = order
        yield bucket.upsert(key, data)


class SearchHandler(tornado.web.RequestHandler):
    http_client = AsyncHTTPClient()

    @tornado.gen.coroutine
    def get(self):

        if fts_nodes:
            query = self.get_query_argument('q')
            query = query.replace('"', r'')
            query = urllib.quote(query)
            terms = query.split()
            query = ' '.join(["{}~1".format(term) for term in terms])
            data = '{"query": {"query": "' + query + '"}, "highlight": null, "fields": null, "facets": null, "explain": false}'
            fts_node = random.choice(fts_nodes)
            request = HTTPRequest(
                url='http://{}:8094/api/index/English/query'.format(fts_node),
                method='POST', body=data, auth_username=settings.ADMIN_USER,
                auth_password=settings.ADMIN_PASS, auth_mode='basic',
                headers={'Content-Type': 'application/json'})
            response = yield self.http_client.fetch(request)

            response = tornado.escape.json_decode(response.body)

            final_results = []
            for hit in response['hits']:
                final_results.append(hit['id'])

            self.write({'keys': final_results})
        else:
            raise Exception('No FTS node found')


class FilterHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        data = self.get_query_argument('type')
        results = yield bucket.n1qlQueryAll(
            'SELECT meta().id FROM {} WHERE category = "{}"'
            .format(bucket_name, data))

        final_results = []
        for row in results:
            final_results.append(row['id'])

        self.write({'keys': final_results})


@tornado.gen.coroutine
def update_cb_status():
    global nodes, fts_enabled, n1ql_enabled, xdcr_enabled, fts_nodes
    # Update the cached node info every 500ms
    while True:
        nodes = yield cb_status.get_node_status()
        n1ql_enabled = yield cb_status.n1ql_enabled()
        xdcr_enabled = yield cb_status.xdcr_enabled()
        fts_nodes = yield cb_status.fts_nodes()
        fts_enabled = yield cb_status.fts_enabled()
        yield tornado.gen.sleep(0.5)

@tornado.gen.coroutine
def update_price_data():
    global price_data, portfolio_cache
    LATEST_TS = 0
    while True:
        call_time = time.time()
        results = yield bucket.n1qlQueryAll(
        'SELECT symbol,price FROM {} WHERE symbol IS NOT MISSING AND price IS NOT MISSING'.format(bucket_name, ))

        final_results = {}
        for row in results:
            price_data[row['symbol']] = float(row['price'])

        res = yield bucket.queryAll(settings.DDOC_NAME, settings.VIEW_NAME,
                                    include_docs=True, descending=False, limit=50,
                                    startkey=LATEST_TS, stale=False)
        new_order = False
        for order in res:
            portfolio_cache.append(order.doc.value)
            LATEST_TS = order.doc.value['ts'] + 1
            print "New Order: ", order.key, order.doc.value['name']

        for portfolio in portfolio_cache:
            portfolio_value = 0
            for stock in portfolio['order']:
                current_price = price_data[stock['symbol']]
                quantity = stock['quantity']
                stock_value = quantity * current_price
                portfolio_value += stock_value
            portfolio['current_value'] = portfolio_value

        result_time = time.time()
        response_time = result_time - call_time
        if response_time < 5: # don't go again til 5s has elaspsed 
            yield tornado.gen.sleep(5 - response_time)

def make_app():
    return tornado.web.Application([
        (r"/", ExchangeHandler),
        (r"/orders", LatestOrdersHandler),
        (r"/stocks", StockLeaderboardHandler),
        (r"/investors", InvestorLeaderboardHandler),
        (r"/nodestatus", CBStatusWebSocket),
        (r"/liveorders", LiveOrdersWebSocket),
        (r"/liveprices", LivePricesWebSocket),
        (r"/stockleaderboard", StockLeaderboardWebSocket),
        (r"/investorleaderboard", InvestorLeaderboardWebSocket),
        (r'/cluster', ClusterVisHandler),
        (r'/submit_order', SubmitHandler),
        (r'/search', SearchHandler),
        (r'/filter', FilterHandler),
        # This is lazy, but will work fine for our purposes
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': "./www/"}),
    ], debug=True)


if __name__ == "__main__":
    print "Running at http://localhost:8888"
    app = make_app()
    app.listen(8888)

    tornado.ioloop.IOLoop.current().spawn_callback(update_cb_status)
    tornado.ioloop.IOLoop.current().spawn_callback(update_price_data)
    tornado.ioloop.IOLoop.current().start()
