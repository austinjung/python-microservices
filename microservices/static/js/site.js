$(function () {

    var mark = function () {

        // Read the keyword
        var keyword = $("input[name='keyword']").val();

        // Determine selected options
        var options = {debug: false, diacritics: true, separateWordSearch: true};

        // Remove previous marked elements and mark
        // the new keyword inside the context
        $(".context_text").unmark({
            done: function () {
                $(".context_text").mark(keyword, options);
            }
        });
    };

    var host_domain_url = window.location.protocol + "//" + window.location.host + "/";
    var inferred_code;
    var inferred_entity_type;

    var sortObject = function (obj) {
        if (typeof obj !== 'object') {
            return obj;
        }
        var temp = {};
        var keys = [];
        for (var key in obj) {
            keys.push(key);
        }
        keys.sort();
        for (var index in keys) {
            temp[keys[index]] = sortObject(obj[keys[index]]);
        }
        return temp;
    };

    var set_disable_all_button = function (disable) {
        $('button').prop('disabled', disable);
    };

    var ajax_infer_next = function (endpoint, data) {
        data = (typeof data !== 'undefined') ?  data : {};
        $.ajax({
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            type: "POST",
            url: host_domain_url + endpoint,
            data: JSON.stringify({}),
            success: function (data, status) {
                if (data.message === 'OK') {
                    var med_code_dropdown = $('#med-code-dropdown');
                    var entity_dropdown = $('#entity-type-dropdown');

                    med_code_dropdown.empty();

                    var suggested_codes = [];
                    entity_dropdown.selectpicker('val', data.results[0].entity_type);
                    inferred_entity_type = data.results[0].entity_type;
                    entity_dropdown.prop('disabled', true);
                    for (var i = 0; i < data.results.length; i++) {
                        var option = document.createElement('option');
                        option.text = data.results[i].code + ": " + data.results[i].preferred_terminology + " (concept_score: " + data.results[i].concept_score + ")";
                        option.value = data.results[i].code;
                        suggested_codes.push(data.results[i].code);
                        med_code_dropdown.append(option);
                    }
                    for (var i_extra = 0; i_extra < data.entity_codes.length; i_extra++) {
                        if (suggested_codes.indexOf(data.entity_codes[i_extra][0]) < 0) {
                            var option_extra = document.createElement('option');
                            option_extra.text = data.entity_codes[i_extra][0] + ": " + data.entity_codes[i_extra][1];
                            option_extra.value = data.entity_codes[i_extra][0];
                            med_code_dropdown.append(option_extra);
                        }
                    }
                    med_code_dropdown.selectpicker('refresh');
                    med_code_dropdown.selectpicker('val', data.results[0].code);
                    inferred_code = data.results[0].code;
                    $("#context_text").html(data.context);
                    $("input[name='extracted-code']").val(data.extracted_code);
                    $("input[name='keyword']").val(data.original_highlighted);
                    set_disable_all_button(false);
                    if (data.extracted_code === null) {
                        $("#accept-extracted-code").prop('disabled', true);
                    }
                    if (data.match_with_extracted) {
                        add_code_match_alert(data.extracted_code);
                        $("#accept-extracted-code").prop('disabled', true);
                    } else if (data.match_with_extracted === false){
                        add_code_mismatch_alert(data.extracted_code, data.results[0].code);
                    }
                } else {
                    set_disable_all_button(false);
                    add_success_alert(data.message);
                    if (data.extracted_code !== null) {
                        $("#accept-extracted-code").prop('disabled', false);
                    }
                    $("#accept-code").prop('disabled', true);
                }
            },
            error: function (error) {
                set_disable_all_button(false);
                add_alert(error.responseJSON.message);
            }
        });
    };

    $(".infer-next").click(function () {
        $("#med-code-detail").val("");
        $("input[name='keyword']").val("");
        set_disable_all_button(true);
        ajax_infer_next("infer_next");
    });

    $("#get-suggestion").click(function () {
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
            success: function (data, status) {
                $("input[name='keyword']").val(data.key_tokens);
                mark();
            }
        });
    });

    $("#accept-code").click(function () {
        if (inferred_code !== $("#med-code-dropdown").val() || inferred_entity_type !== $("#entity-type-dropdown").val()) {
            add_alert("Inferred code or entity type was changed.");
            return
        }
        $("#med-code-detail").val("");
        $("input[name='keyword']").val("");
        set_disable_all_button(true);
        ajax_infer_next("accept_and_process_next");
    });

    $("#accept-extracted-code").click(function () {
        $("#med-code-detail").val("");
        $("input[name='keyword']").val("");
        set_disable_all_button(true);
        ajax_infer_next("accept_extractor_and_process_next");
    });

    $("#reject-all").click(function () {
        var new_entity_type = $("#entity-type-dropdown").val();
        var new_code = $("#med-code-dropdown").val();
        if (inferred_code === new_code || inferred_entity_type === new_entity_type) {
            add_alert("Inferred code or entity type was not changed.");
            return;
        }
        $("#med-code-detail").val("");
        $("input[name='keyword']").val("");
        set_disable_all_button(true);
        data = {
            new_code: new_code,
            new_entity_type: new_entity_type
        };
        ajax_infer_next("reject_and_learn", data);
    });

    $("input[name='keyword']").on("input", mark);

    $('#med-code-dropdown').on("changed.bs.select", function(e, clickedIndex, newValue, oldValue) {
        var data = {
            entity_type: $('#entity-type-dropdown option:selected').val(),
            code: this.value
        };
        $.ajax({
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            type: "POST",
            url: host_domain_url + "terminology_code",
            data: JSON.stringify(data),
            success: function (data, status) {
                if (data.message === 'OK') {
                    $('#med-code-synonyms').html(data.synonyms);
                    $('#med-code-relations').html(data.relations);
                } else {
                    add_success_alert(data.message);
                }
            },
            error: function (error) {
                set_disable_all_button(false);
                add_alert(error.responseJSON.message);
            }
        });
    });

    var add_alert = function (message) {
        var message_block = $('#message-block');
        var alert_div = document.createElement('div');
        $(alert_div).addClass("alert");
        var button = document.createElement('span');
        $(button).addClass("closebtn");
        $(button).html("&times;");
        $(alert_div).append(button);
        $(alert_div).append("<strong>Danger!</strong> " + message);
        message_block.append(alert_div);
        button.onclick = function () {
            var div = this.parentElement;
            div.style.opacity = "0";
            setTimeout(function () {
                div.style.display = "none";
            }, 600);
        };
    };

    var add_success_alert = function (message) {
        var message_block = $('#message-block');
        var alert_div = document.createElement('div');
        $(alert_div).addClass("alert success");
        var button = document.createElement('span');
        $(button).addClass("closebtn");
        $(button).html("&times;");
        $(alert_div).append(button);
        $(alert_div).append("<strong>Success!</strong> " + message);
        message_block.append(alert_div);
        button.onclick = function () {
            var div = this.parentElement;
            div.style.opacity = "0";
            setTimeout(function () {
                div.style.display = "none";
            }, 600);
        };
    };

    var add_code_match_alert = function (code) {
        var message_block = $('#message-block');
        var alert_div = document.createElement('div');
        $(alert_div).addClass("alert success");
        var button = document.createElement('span');
        $(button).addClass("closebtn");
        $(button).html("&times;");
        $(alert_div).append(button);
        $(alert_div).append("<strong>Code matched!</strong> " + code);
        message_block.append(alert_div);
        setTimeout(function () {
            alert_div.style.display = "none";
        }, 3600);
        button.onclick = function () {
            var div = this.parentElement;
            div.style.opacity = "0";
            setTimeout(function () {
                div.style.display = "none";
            }, 600);
        };
    };

    var add_code_mismatch_alert = function (code1, code2) {
        var message_block = $('#message-block');
        var alert_div = document.createElement('div');
        $(alert_div).addClass("alert");
        var button = document.createElement('span');
        $(button).addClass("closebtn");
        $(button).html("&times;");
        $(alert_div).append(button);
        $(alert_div).append("<strong>Code mismatch!</strong> " + code1 + ", " + code2);
        message_block.append(alert_div);
        setTimeout(function () {
            alert_div.style.display = "none";
        }, 3600);
        button.onclick = function () {
            var div = this.parentElement;
            div.style.opacity = "0";
            setTimeout(function () {
                div.style.display = "none";
            }, 600);
        };
    };

});
