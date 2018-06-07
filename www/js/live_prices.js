// Open a web socket to the server to receive live price updates
// On recipt of an update, search the page for any instances of the symbol
// And update the price accordingly.
var prices_ws = null;

$(document).ready(function(){
  prices_ws = new WebSocket("ws://" + location.host + "/liveprices");

  prices_ws.onopen = function() 
  {
    console.log("Live Prices started");
  };

  prices_ws.onmessage = function (evt)
  {
    var msg = JSON.parse(evt.data);
    for (var symbol in msg) 
    {
      if (msg.hasOwnProperty(symbol))  // SO says do this
      { 
        price_elem = "." + symbol + "-price";
        btn_elem = "#" + symbol + "-btn";
        cur_price = parseFloat( $(price_elem).text().substring(1) );
        new_price = parseFloat(msg[symbol]['price']);
        change = parseFloat(msg[symbol]['change']);
        if (change >= 0)
        {
            $(btn_elem).removeClass("btn-danger");
            $(btn_elem).addClass("btn-success");
        }
        else {
            $(btn_elem).removeClass("btn-success");
            $(btn_elem).addClass("btn-danger");  
        }
        $(btn_elem).text(change + "%");
        $(price_elem).text('£'+new_price);
      }
    }
  };

  prices_ws.onclose = function()
  {
      // websocket is closed.
      // setTimeout(function(){ExchangePageWebSockets()}, 5000);
  };
});
