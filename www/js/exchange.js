var table = null;
var filtered_keys = [];
var currently_selected = [];

$( ".submit-btn" ).click(function() {
    var name_box = $("#name-box");

    if (!name_box.val()){
        alert("Please enter a name before submitting.");
        return;
    }
    if (currently_selected.length < 5){
        alert("Please select 5 items before submitting.");
        return;
    }

    $.post( "/submit_order",
        JSON.stringify({
            name: name_box.val(),
            order: currently_selected}),
        function( data ) {
            alert("Order submitted!");
            $(".btn-product.active").removeClass("active");
            currently_selected = [];
        })
        .fail(function () {
            alert("Error submitting order.")
        });
});

$( ".btn-product" ).click(function (event){
    if (currently_selected.length >= 5) {
        if (!$(this).hasClass("active")) {
            alert("Cannot select more than 5 items.");
            event.stopPropagation();
        } else {
             var i = currently_selected.indexOf($(this).val());
             currently_selected.splice(i, 1);
         }

    } else {
         if (!$(this).hasClass("active")) {
             currently_selected.push($(this).val());
         } else {
             var i = currently_selected.indexOf($(this).val());
             currently_selected.splice(i, 1);
         }
    }
});


var clear_types = function (){
    $(".type-btn").each(function () {
        $(this).removeClass("active");
    });
};

function hasTouch() {
    return "ontouchstart" in window || window.navigator.msMaxTouchPoints > 0;
}

if (hasTouch()) { // remove all :hover stylesheets
    try { // prevent exception on browsers not supporting DOM styleSheets properly
        for (var si in document.styleSheets) {
            var styleSheet = document.styleSheets[si];
            if (!styleSheet.rules) continue;

            for (var ri = styleSheet.rules.length - 1; ri >= 0; ri--) {
                if (!styleSheet.rules[ri].selectorText) continue;

                if (styleSheet.rules[ri].selectorText.match(':hover')) {
                    styleSheet.deleteRule(ri);
                }
            }
        }
    } catch (ex) {
    }
}

$(".search-btn").click(function() {
    if($('.search-input').val() === ""){
        clear_types();
        filtered_keys = [];
        table.draw();
        return;
    }
    clear_types();
    $(".search-btn").attr("disabled", true);
    $("body > div > div > div > div > div.container > div:nth-child(1) > div.col-md-4.col-sm-6.col-8.search-container > button > img").addClass("rotate");
    $.get("/search?q="+$(".search-input").val(), function (data){
        filtered_keys = data['keys'];
        table.draw();
    }).fail(function(){
        alert("Error submitting search.")
    }).always(function (){
        $("body > div > div > div > div > div.container > div:nth-child(1) > div.col-md-4.col-sm-6.col-8.search-container > button > img").removeClass("rotate");
        $(".search-btn").attr("disabled", false);
    });
});

$(".type-btn").click(function(){
    $('.search-input').val('');

    clear_types();
    $.get("/filter?type=" + $(this).val(), function (data){
        filtered_keys = data['keys'];
        table.draw();
    });

});

$(".type-row").hover(function(){
    $(this).css("border-style", "none");
});

$(".type-row").click(function(){
    $(this).css("border-style", "none");
});

$(".search-container").hover(function(){
    $(this).css("border-style", "none");
});

$(".search-container").click(function(){
    $(this).css("border-style", "none");
});

$(document).ready(function(){
    $('#name-box').keypress(function(e){
        if(e.keyCode==13)
            $('.submit-btn').click();
    });
});

$(document).ready(function(){
    $('.search-input').keypress(function(e){
        if(e.keyCode==13)
            $('.search-btn').click();
    });
});

$(document).ready(function(){
    $('.search-input').on('input', function(e){
        if($('.search-input').val() === ""){
        clear_types();
        filtered_keys = [];
        table.draw();
        }
    });
});

$(document).ready(function() {
    table = $('#stocks_table').DataTable({"pageLength": 20,"lengthChange":false, "ordering":false,"dom": 'lrtip',
    "drawCallback": function(settings){
         $(".btn-product.active").each(function(index){
             if (currently_selected.indexOf($(this).val()) === -1){
                 $(this).removeClass("active");
             }
         });
    }});
    $.fn.dataTable.ext.search.push(
        function( settings, data, dataIndex ) {
            var button = data[0];
            button = "stock:" + $.trim(button);
            return (filtered_keys.indexOf(button) !== -1 || filtered_keys.length === 0);
    });
} );

window.onload = function ExchangePageWebSockets(){
// One web socket to get the nodes statuses, another web socket to get the live price info

    if ("WebSocket" in window) {
        // Let us open a web socket
        var nodes_ws = new WebSocket("ws://" + location.host + "/nodestatus");


        nodes_ws.onopen = function() {
            console.log("started");
            // Web Socket is connected, send data using send()
            nodes_ws.send("Exchange Node Status Socket Connected");
        };

        nodes_ws.onmessage = function (evt)
        {
            var msg = JSON.parse(evt.data);
            if (msg['fts']){
                $(".search-container").show();
            } else {
                $(".search-container").hide();
            }

            if (msg['n1ql']){
                $(".type-row").show();
            } else {
                $(".type-row").hide();
            }

        };

        nodes_ws.onclose = function()
        {
            // websocket is closed.
            // setTimeout(function(){ExchangePageWebSockets()}, 5000);
        };



    }
    else
    {
        // The browser doesn't support WebSocket
        alert("WebSocket NOT supported by your Browser!");
    }
};