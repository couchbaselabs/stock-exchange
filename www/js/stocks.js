// Open a web socket to the server to receive live price updates
// On recipt of an update, search the page for any instances of the symbol
// And update the price accordingly.
$(document).ready(function(){
  var stock_leaderboard_ws = new WebSocket("ws://" + location.host + "/stockleaderboard");

  stock_leaderboard_ws.onopen = function() 
  {
    console.log("Stock Leaderboard started");
    // Web Socket is connected, send data using send()
    stock_leaderboard_ws.send("Stock Leaderboard Socket Connected");
  };

  stock_leaderboard_ws.onmessage = function (evt)
  {
    var msg = JSON.parse(evt.data);
    for (i = 0; i < 10; i++){
      $('#top-row-'+i).find(".symbol").text(msg['best'][i]['symbol']);
      $('#top-row-'+i).find(".starting").text(msg['best'][i]['starting_price']);
      $('#top-row-'+i).find(".price").text(msg['best'][i]['price']);
      $('#top-row-'+i).find(".diff").text(msg['best'][i]['price_diff'].toFixed(2) + "%");
      $('#worst-row-'+i).find(".symbol").text(msg['worst'][i]['symbol']);
      $('#worst-row-'+i).find(".starting").text(msg['worst'][i]['starting_price']);
      $('#worst-row-'+i).find(".price").text(msg['worst'][i]['price']);
      price_diff = msg['worst'][i]['price_diff'].toFixed(2);
      if (price_diff < 0)
      {
        $('#worst-row-'+i).find(".diff").removeClass("btn-success");
        $('#worst-row-'+i).find(".diff").addClass("btn-danger");  
      }
      $('#worst-row-'+i).find(".diff").text(price_diff + "%");
    }
  };

  stock_leaderboard_ws.onclose = function()
  {
      // websocket is closed.
      // setTimeout(function(){ExchangePageWebSockets()}, 5000);
  };
});