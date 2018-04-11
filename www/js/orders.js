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
            $(document).find("td").text("HEY HEY");
            console.log(slideIndex);
            var new_elem = $('#master-slide').clone();
            var msg = JSON.parse(evt.data);
            images=msg['images']
            new_elem.attr('id',slideIndex);
            slideIndex++;
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
