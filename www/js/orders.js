var slideIndex = 0

window.onload = function N1QLSocket(){
    if ("WebSocket" in window) {
        // Let us open a web socket
        var ws = new WebSocket("ws://" + location.host + "/liveorders");
        ws.onopen = function() {
            // Web Socket is connected, send data using send()
            ws.send("Bingo Bango");
        };

        ws.onmessage = function (evt)
        {
          //  $(document).find("td").text("HEY HEY");
            var new_elem = $('#master-slide').clone();
            var msg = JSON.parse(evt.data);
            var order = msg['order'];
            new_elem.attr('id',slideIndex);
            slideIndex++;
            for (i = 0; i <5; i++ )
            {
                var row_elem = $(new_elem).find("#stock-" + i);
                symbol_name = msg['order'][i]['symbol'];
                purchase_price = msg['order'][i]['purchase_price'];
                row_elem.find(".symbol").text(symbol_name);
                row_elem.find(".purchase").text('$'+purchase_price);
                row_elem.find(".price").addClass(symbol_name + '-price');
            }
            $(new_elem).find("h3").text(msg['name']);
            $('.multiple-items').slick('slickAdd',new_elem);
            $('.multiple-items').slick('slickNext');
        };

        ws.onclose = function()
        {
            // websocket is closed.
            $("#unhappy-shopper").text("Ready");
            $("#happy-shopper").text("Please place an order");
            setTimeout(function(){N1QLSocket()}, 5000);
        };
    }

    else
    {
        // The browser doesn't support WebSocket
        alert("WebSocket NOT supported by your Browser!");
    }
}

$(document).ready(function(){
      $('.multiple-items').slick({
          slidesToShow: 3,
          slidesToScroll: 1   });
    });
