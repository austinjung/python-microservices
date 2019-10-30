$(function() {

  var mark = function() {

    // Read the keyword
    var keyword = $("input[name='keyword']").val();

    // Determine selected options
    var options = {debug: false, diacritics: true, separateWordSearch: true};

    // Remove previous marked elements and mark
    // the new keyword inside the context
    $(".context").unmark({
      done: function() {
        $(".context").mark(keyword, options);
      }
    });
  };

  var possibleOptions;

  var sortObject = function(obj) {
    if(typeof obj !== 'object')
        return obj;
    var temp = {};
    var keys = [];
    for(var key in obj)
        keys.push(key);
    keys.sort();
    for(var index in keys)
        temp[keys[index]] = sortObject(obj[keys[index]]);
    return temp;
  };

  $("#get-codes").click(function(){
        var concept = $.trim($("input[name='keyword']").val());
        var context = $.trim($("#context").val());
        var entity_type = "";
        $("#med-code-detail").val("");
        $.each($("#entity-type-dropdown option:selected"), function(){
          if ($(this).val() !== "")
            entity_type = entity_type + "," + $(this).val();
        });
        $.ajax({
          dataType: "json",
          contentType: "application/json; charset=utf-8",
          type: "POST",
          url: "http://localhost:5000/find_codes",
          data: JSON.stringify({
            concept_text: concept,
            context_text: context,
            entity_type: entity_type
          }),
          success: function(data, status){
            var dropdown = $('#med-code-dropdown');

            dropdown.empty();
            dropdown.append('<option selected>Choose med code</option>');
            dropdown.prop('selectedIndex', 0);

            possibleOptions = {};
            for (var i = 0; i < data.results.length; i++) {
              var option = document.createElement('option');
              option.text = data.results[i].code + ": " + data.results[i].entity_type + ": " + data.results[i].terminology + ": " + data.results[i].synonym;
              data.results[i].code_details.Code = data.results[i].code;
              data.results[i].code_details.Terminology = data.results[i].terminology;
              data.results[i].code_details.Entity_type = data.results[i].entity_type;
              possibleOptions[data.results[i].code] = sortObject(data.results[i].code_details);
              option.value = data.results[i].code;
              dropdown.append(option);
            }
            var pretty = JSON.stringify(possibleOptions[data.results[0].code], undefined, 8);
            $("#med-code-detail").val(pretty);
            $('#med-code-dropdown').val(data.results[0].code);
          }
        });
      });

  $("#get-suggestion").click(function(){
        var context = $.trim($("#context").val());
        $("#highlighted").text(context);
        $.ajax({
          dataType: "json",
          contentType: "application/json; charset=utf-8",
          type: "POST",
          url: "http://localhost:5000/get_terminologies",
          data: JSON.stringify({
            context: context
          }),
          success: function(data,status){
            $("input[name='keyword']").val(data.key_tokens);
            mark();
          }
        });
  });

  $("input[name='keyword']").on("input", mark);

  $('#med-code-dropdown').change(function(){
    var selectedCode = $(this).children("option:selected").val();
    var pretty = JSON.stringify(possibleOptions[selectedCode], undefined, 8);
    $("#med-code-detail").val(pretty);
  });

  var add_alert = function(message) {
      var message_block = $('#message-block');
      var alert_div = document.createElement('div');
      $(alert_div).addClass("alert");
      var button = document.createElement('span');
      $(button).addClass("closebtn");
      $(button).html("&times;");
      $(alert_div).append(button);
      $(alert_div).append("<strong>Danger!</strong> " + message);
      message_block.append(alert_div);
      button.onclick = function(){
          var div = this.parentElement;
          div.style.opacity = "0";
          setTimeout(function(){ div.style.display = "none"; }, 600);
      };
  };

  var add_success_alert = function(message) {
      var message_block = $('#message-block');
      var alert_div = document.createElement('div');
      $(alert_div).addClass("alert success");
      var button = document.createElement('span');
      $(button).addClass("closebtn");
      $(button).html("&times;");
      $(alert_div).append(button);
      $(alert_div).append("<strong>Success!</strong> " + message);
      message_block.append(alert_div);
      button.onclick = function(){
          var div = this.parentElement;
          div.style.opacity = "0";
          setTimeout(function(){ div.style.display = "none"; }, 600);
      };
  };

});
