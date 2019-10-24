$(function() {

  var mark = function() {

    // Read the keyword
    var keyword = $("input[name='keyword']").val();

    // Determine selected options
    var options = {debug: false, diacritics: true, separateWordSearch: true};
    // $("input[name='opt[]']").each(function() {
    //   options[$(this).val()] = $(this).is(":checked");
    // });

    // Remove previous marked elements and mark
    // the new keyword inside the context
    $(".context").unmark({
      done: function() {
        $(".context").mark(keyword, options);
      }
    });
  };

  $("#get-codes").click(function(){
        var concept = $.trim($("input[name='keyword']").val());
        var context = $.trim($("#context").val());
        var entity_type = "";
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

            for (var i = 0; i < data.results.length; i++) {
              var option = document.createElement('option');
              option.text = data.results[i].code + ": " + data.results[i].synonym;
              option.value = data.results[i].code;
              dropdown.append(option);
            }
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
  // $("input[type='checkbox']").on("change", mark);

});
