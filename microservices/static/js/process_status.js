$(function () {
    'use strict';

    $('input:checkbox').click(function() {
        var id = $(this).attr('id');
        if (id === 'select-all-input') {
            $('input:checkbox').not(this).prop('checked', $(this).prop('checked'));
        } else {
            $('input:checkbox').not(this).prop('checked', false);
            if ($(this).prop('checked')) {
                $(this).prop('checked', true);
            } else {
                $(this).prop('checked', false);
            }
        }
    });

    $("#view-dataset").click(function () {
        var id = $( "input:checked" ).first().attr('id');
        $(location).attr('href', '/view/' + id);
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
            location.reload();
        };
    };

    $("#delete-dataset").click(function () {
        var id = $( "input:checked" ).first().attr('id');
        var endpoint = '/delete/' + id;
        $.ajax({
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            type: "POST",
            url: endpoint,
            data: JSON.stringify({}),
            success: function (data, status) {
                add_success_alert(data.message);
                setTimeout(function () {
                    location.reload();
                }, 600);
            },
            error: function (error) {
                add_alert(error.responseJSON.message);
            }
        });

    });

    $("#select-dataset").click(function () {
        var id = $( "input:checked" ).first().attr('id');
        var endpoint = '/set_dataset_and_infer_next';
        $.ajax({
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            type: "POST",
            url: endpoint,
            data: JSON.stringify({selected_dataset: id}),
            success: function (data, status) {
                add_success_alert(data.message);
                setTimeout(function () {
                    location.href = '/?auto-process=true';
                }, 600);
            },
            error: function (error) {
                add_alert(error.statusText);
            }
        });

    });
});
