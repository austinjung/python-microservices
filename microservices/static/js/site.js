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

    var $med_code_dropdown = $('#med-code-dropdown');

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

    var set_disable_all_buttons = function (disable) {
        var buttons = $('.action-button');
        buttons.addClass('d-none');
        $("input[name='new-code']").addClass('d-none');
        $("input[name='new-code-terminology']").addClass('d-none');
        $("#get-new-code").addClass('d-none');
        $(".end-of-document-button").addClass('d-none');
        $("#get-pipeline-code-detail").attr("disabled", true);
        $("#get-t2-code-detail").attr("disabled", true);
        $("#copy-code-to-learn").addClass('d-none');
    };
    var preset_enable_buttons = ['get-pipeline-code-detail', 'get-t2-code-detail'];
    var preset_enable_all_button = function () {
        preset_enable_buttons = ['get-pipeline-code-detail', 'get-t2-code-detail'];
        $('.action-button').each(function(idx, btn){
            preset_enable_buttons.push($(btn).attr('id'));
        });
    };
    var preset_disable_button = function (btn_id) {
        var index = preset_enable_buttons.indexOf(btn_id);
        if (index >= 0) {
            preset_enable_buttons.splice(preset_enable_buttons.indexOf(btn_id), 1);
        }
    };
    var enable_preset_buttons = function () {
        $.each( preset_enable_buttons, function( idx, btn_id ){
            var btn = $('#' + btn_id);
            if (btn_id === 'get-pipeline-code-detail') {
                $("#get-pipeline-code-detail").attr("disabled", false);
            } else if (btn_id === 'get-t2-code-detail') {
                $("#get-t2-code-detail").attr("disabled", false);
            } else {
                btn.removeClass('d-none');
            }
        });
    };
    var enable_button = function (btn_id) {
        var btn = $('#' + btn_id);
        btn.removeClass('d-none');
    };

    var trimString = function (string, length) {
      return string.length > length ?
             string.substring(0, length) + '...' :
             string;
    };

    var ajax_infer_next = function (endpoint, data) {
        var closebtn = $(".closebtn");
        if (closebtn.length > 0) {
            closebtn.click();
        }
        $("input[name='pipeline-extracted-code']").val("");
        $("input[name='pipeline-entity-type']").val("");
        $("input[name='pipeline-keyword']").val("");
        $("input[name='t2-extracted-code-input']").val("");
        $("input[name='t2-keyword']").val("");
        $("input[name='new-code']").val("");
        $("input[name='new-code-terminology']").val("");
        set_disable_all_buttons(true);
        data = (typeof data !== 'undefined') ?  data : {};
        $.ajax({
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            type: "POST",
            url: host_domain_url + endpoint,
            data: JSON.stringify(data),
            success: function (data, status) {
                if (data.message === 'OK') {
                    var t2_entity_dropdown = $('#t2-entity-type-dropdown');

                    $med_code_dropdown.empty();

                    var suggested_codes = [];
                    t2_entity_dropdown.selectpicker('val', data.entity_type);
                    if (data.results.length > 0) {
                        inferred_entity_type = data.results[0].entity_type;
                        inferred_code = data.results[0].code;
                        $("input[name='t2-extracted-code-input']").val(inferred_code);
                        for (var i = 0; i < data.results.length; i++) {
                            var option = document.createElement('option');
                            option.text = data.results[i].code + ": " + data.results[i].preferred_terminology + " (concept_score: " + data.results[i].concept_score.toFixed(4) + ")";
                            option.value = data.results[i].code;
                            suggested_codes.push(data.results[i].code);
                            $med_code_dropdown.append(option);
                        }
                    } else {
                        inferred_entity_type = null;
                        inferred_code = null;
                    }
                    var extracted_code_not_exist = true;
                    for (var i_extra = 0; i_extra < data.entity_codes.length; i_extra++) {
                        if (data.entity_codes[i_extra][0] === inferred_code) {
                            extracted_code_not_exist = false;
                        }
                        if (suggested_codes.indexOf(data.entity_codes[i_extra][0]) < 0) {
                            var option_extra = document.createElement('option');
                            option_extra.text = data.entity_codes[i_extra][0] + ": " + trimString(data.entity_codes[i_extra][1], 50);
                            option_extra.value = data.entity_codes[i_extra][0];
                            $med_code_dropdown.append(option_extra);
                        }
                    }
                    $med_code_dropdown.selectpicker('refresh');
                    if (data.results.length > 0) {
                        $med_code_dropdown.selectpicker('val', data.results[0].code);
                    }
                    var current_processing = $("#current_processing");
                    current_processing.text("Current processing: " + data.current_process);
                    current_processing.attr("href", "/view/" + data.current_process);
                    $("#context_text").html(data.context);
                    $("input[name='pipeline-extracted-code']").val(data.extracted_code);
                    $("input[name='pipeline-entity-type']").val(data.entity_type);
                    $("input[name='pipeline-keyword']").val(data.original_highlighted);
                    if (data.results.length > 0) {
                        $("input[name='t2-keyword']").val(data.results[0].synonym);
                    }
                    preset_enable_all_button();
                    if (data.extracted_code === null) {
                        preset_disable_button("accept-pipeline-code");
                        preset_disable_button("get-pipeline-code-detail");
                        preset_disable_button("accept-code");
                    }
                    if (data.match_with_extracted) {
                        add_code_match_alert(data.extracted_code);
                        preset_disable_button("accept-pipeline-code");
                        preset_disable_button("get-pipeline-code-detail");
                        preset_disable_button("accept-t2-code");
                        preset_disable_button("get-t2-code-detail");
                    }
                    if (data.match_with_extracted === false && data.results.length > 0) {
                        add_code_mismatch_alert(data.extracted_code, data.results[0].code);
                        preset_disable_button("accept-code");
                    }
                    if (data.extracted_code === "") {
                        preset_disable_button("accept-code");
                        preset_disable_button("accept-pipeline-code");
                        preset_disable_button("get-pipeline-code-detail");
                    }
                    if (data.results.length === 0) {
                        add_alert("No code matched");
                        preset_disable_button("accept-code");
                        preset_disable_button("accept-t2-code");
                    }
                    if (extracted_code_not_exist) {
                        add_alert("Pipeline extracted code not exist in Ciitizen terminology code");
                        preset_disable_button("accept-pipeline-code");
                        preset_disable_button("get-pipeline-code-detail");
                    }
                    enable_preset_buttons();
                } else {
                    add_alert(data.message);
                    $(".end-of-document-button").removeClass('d-none');
                }
            },
            error: function (error) {
                enable_button("reprocess");
                enable_button("skip-code");
                add_alert(error.responseJSON.message);
            }
        });
    };

    $(".infer-next").click(function () {
        ajax_infer_next("infer_next");
    });

    $("#get-suggestion").click(function () {
        var context = $.trim($("#context").val());
        $("#highlighted").text(context);
        $.ajax({
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            type: "POST",
            url: host_domain_url + "get_terminologies",
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
        if (inferred_code !== $med_code_dropdown.val() || inferred_entity_type !== $("#t2-entity-type-dropdown").val()) {
            add_alert("Inferred code or entity type was changed.");
            return;
        }
        ajax_infer_next("accept_and_process_next");
    });

    $("#accept-t2-code").click(function () {
        ajax_infer_next("accept_and_process_next");
    });

    $("#skip-code").click(function () {
        ajax_infer_next("skip");
    });

    $("#accept-pipeline-code").click(function () {
        $("input[name='keyword']").val("");
        ajax_infer_next("accept_extractor_and_process_next");
    });

    $("#copy-code-to-learn").click(function () {
        $("input[name='new-code']").val($med_code_dropdown.val());
    });

    $("#get-pipeline-code-detail").click(function () {
        $med_code_dropdown.selectpicker('val', $("input[name='pipeline-extracted-code']").val());
    });

    $("#get-t2-code-detail").click(function () {
        $med_code_dropdown.selectpicker('val', $("input[name='t2-extracted-code-input']").val());
    });

    var learn = function ($this) {
        var new_code_terminology = $("input[name='new-code-terminology']").val();
        var new_code = $("input[name='new-code']").val();
        var pipeline_code = $("input[name='pipeline-extracted-code']").val();
        if (new_code === "" || new_code === null) {
            new_code = $med_code_dropdown.val();
        }
        // if (inferred_code === new_code) {
        //     add_alert("Inferred code or entity type was not changed.");
        //     $(".end-of-document-button").addClass('d-none');
        //     return;
        // }
        // if (pipeline_code === new_code) {
        //     add_alert("Changed code is the same as pipeline code.");
        // }
        var highlighted = $("input[name='t2-keyword']").val();
        var data = {
            new_code: new_code,
            new_code_terminology: new_code_terminology,
            highlighted: highlighted
        };
        $this.toggleClass('learn');
        $this.text('Reject both');
        ajax_infer_next("reject_and_learn", data);
    };

    $("#reject-all").click(function () {
        var $this = $(this);
        if($this.hasClass('learn')) {
            learn($this);
        } else {
            $this.text('Learn');
            $this.toggleClass('learn');
            $("input[name='new-code']").removeClass('d-none');
            $("input[name='new-code-terminology']").removeClass('d-none');
            $("#get-new-code").removeClass('d-none');
            $("#copy-code-to-learn").removeClass('d-none');
        }
    });

    $("input[name='keyword']").on("input", mark);

    $med_code_dropdown.on("changed.bs.select", function(e, clickedIndex, newValue, oldValue) {
        var data = {
            entity_type: $('#t2-entity-type-dropdown option:selected').val(),
            code: this.value
        };
        // $("input[name='t2-extracted-code-input']").val($med_code_dropdown.val());
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
                add_alert(error.responseJSON.message);
            }
        });
    });

    var add_alert = function (message) {
        var message_block = $('#message-block');
        var alert_div = document.createElement('div');
        $(alert_div).addClass("alert warning");
        var button = document.createElement('span');
        $(button).addClass("closebtn");
        $(button).html("&times;");
        $(alert_div).append(button);
        $(alert_div).append("<strong>Warning!</strong> " + message);
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
        // setTimeout(function () {
        //     alert_div.style.display = "none";
        // }, 3600);
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
        $(alert_div).addClass("alert warning");
        var button = document.createElement('span');
        $(button).addClass("closebtn");
        $(button).html("&times;");
        $(alert_div).append(button);
        $(alert_div).append("<strong>Code mismatch!</strong> " + code1 + ", " + code2);
        message_block.append(alert_div);
        // setTimeout(function () {
        //     alert_div.style.display = "none";
        // }, 3600);
        button.onclick = function () {
            var div = this.parentElement;
            div.style.opacity = "0";
            setTimeout(function () {
                div.style.display = "none";
            }, 600);
        };
    };

    if ($("#auto-process").length > 0) {
        ajax_infer_next("infer_next");
    }

    $(".panel-left").resizable({
        handleSelector: ".splitter",
        resizeHeight: false
    });

    $(".panel-top").resizable({
        handleSelector: ".splitter-horizontal",
        resizeWidth: false
    });

    $med_code_dropdown.on('shown.bs.select', function (e, clickedIndex, isSelected, previousValue) {
        var $drop_down = $('.dropdown-menu.show');
        $drop_down.css('min-width', '600px');
        $drop_down.css('left', '350px');
    });

});
