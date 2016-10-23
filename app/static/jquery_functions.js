/**
 * Created by vtsymbal on 27.09.2016.
 */
$(document).ready(function(){
  $(".contact-hiden").click(function(){
    var t = $(this),
        div = $(this).parents("div"),
        e = div.attr("data-bid-id"),
        sesion = $("#tops"),
        currency = sesion.attr("currency"),
        operation = sesion.attr("operation"),
        number = t.text();
        // $.post("/api/mincontacts" , JSON.stringify({
        //   bid: e,
        //   action: "auction-get-contacts",
        //   r: !0
        // }));
        $.ajax({
        type: "POST",
        contentType: "application/json",
        url: '/api/mincontacts',
        data: JSON.stringify({ bid: e, currency: currency, operation: operation, number: number}),
        dataType: "json",
        success: function(response, statusTxt, xhr) {
                    if (response['code'] == 0){
                       // alert("Error: " + xhr.status + ": " + xhr.statusText + "jj" + response['number']);
                        t.text(number.replace("xxx-x", "-" + response['data']));
                        t.addClass("contact-shown");
                        t.removeClass("contact-hiden");
                        // t.remove();

                    }
                }
        });
  });
  $(".hide-button").click(function () {
      var div = $(this).parents("div"),
      bid = div.attr("data-bid-id"),
      source = div.attr("source");
      $(this).parents("div").hide("slow", function () {
          $.ajax({
            type: "POST",
            contentType: "application/json",
            url: '/api/hide',
            data: JSON.stringify({ bid: bid, source: source, hide: true}),
            dataType: "json"
          });
      });

  });
    $(".unhide-button").click(function () {
      var div = $(this).parents("div"),
      bid = div.attr("data-bid-id"),
      source = div.attr("source");
      $(this).parents("div").hide("slow", function () {
          $.ajax({
            type: "POST",
            contentType: "application/json",
            url: '/api/hide',
            data: JSON.stringify({ bid: bid, source: source, hide: false}),
            dataType: "json"
          });
      });

  });
});

// $(document).ready(function(){
//     $(".au-dealer-phone-xxx").click(function(){
//         $(this).hide();
//     });
// });


