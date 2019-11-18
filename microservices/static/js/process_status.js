$(function () {
    'use strict';

    $('input:checkbox').click(function() {
        var id = $(this).attr('id');
        if (id === 'select-all-input') {
            $('input:checkbox').not(this).prop('checked', $(this).prop('checked'));
        }
    });

    var get_selected_ids = function() {
        var selected_ids = [];
        $( "input:checked" ).each(function(idx, obj){
            if ($(obj).attr('id') !== 'select-all-input') {
                selected_ids.push($(obj).attr('id'));
            }
        });
        return selected_ids;
    };

    $("#view-dataset").click(function () {
        var id = get_selected_ids()[0];
        if (id === undefined) {
            add_alert('Please select file fisrt.');
            return;
        }
        $(location).attr('href', '/view/' + id);
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
            location.reload();
        };
    };

    $("#delete-dataset").click(function () {
        var ids = get_selected_ids();
        if (ids.length === 0) {
            add_alert('Please select file fisrt.');
            return;
        }
        $.each(ids, function( idx, file_id ) {
            var endpoint = '/delete/' + file_id;
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
    });

    $("#select-dataset").click(function () {
        var id = get_selected_ids()[0];
        if (id === undefined) {
            add_alert('Please select file fisrt.');
            return;
        }
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
