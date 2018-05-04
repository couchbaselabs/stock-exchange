// Open a web socket to the server to receive live price updates
// On recipt of an update, search the page for any instances of the symbol
// And update the price accordingly.
$(document).ready(function(){
  var investor_leaderboard_ws = new WebSocket("ws://" + location.host + "/investorleaderboard");

  investor_leaderboard_ws.onopen = function() 
  {
    console.log("Investor Leaderboard started");
    // Web Socket is connected, send data using send()
    investor_leaderboard_ws.send("Investor Leaderboard Socket Connected");
  };

  investor_leaderboard_ws.onmessage = function (evt)
  {
    var msg = JSON.parse(evt.data);
    for (i = 0; i < 5; i++){
      $('#top-row-'+i).find(".investor").text(msg['best'][i]['name']);
      $('#top-row-'+i).find(".portfolio_value").text('$' + msg['best'][i]['current_value'].toFixed(0));
      $('#worst-row-'+(4-i)).find(".investor").text(msg['worst'][i]['name']);
      $('#worst-row-'+(4-i)).find(".portfolio_value").text('$' + msg['worst'][i]['current_value'].toFixed(0));
    }
  };

  investor_leaderboard_ws.onclose = function()
  {
      // websocket is closed.
      // setTimeout(function(){ExchangePageWebSockets()}, 5000);
  };
});

jQuery(document).ready(function($) {
    $(".clickable-row").click(function() {
        window.location = $(this).data("href");
    });
});