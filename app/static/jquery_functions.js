/**
 * Created by vtsymbal on 27.09.2016.
 */
$(document).ready(function(){
  $(".contact-hiden").click(function(){
    var t = $(this),
        e = t.attr("data-bid-id"),
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
                        t.text(number.replace("xxx-x", response['data']));
                        t.addClass("contact-shown");
                        t.removeClass("contact-hiden");
                        // t.remove();

                    }
                }
        });
  });
});

// $(document).ready(function(){
//     $(".au-dealer-phone-xxx").click(function(){
//         $(this).hide();
//     });
// });


