$(function () {
    'use strict';

    var dropZone = document.getElementById('drop-zone');
    var uploadForm = document.getElementById('js-upload-form');

    var host_domain_url = window.location.protocol + "//" + window.location.host + "/";

    var progressHandling = function (event) {
        var percent = 0;
        var position = event.loaded || event.position;
        var total = event.total;
        var progress = ".progress";
        if (event.lengthComputable) {
            percent = Math.ceil(position / total * 100);
        }
        // update progressbars classes so it fits your code
        $(".progress .progress-bar").css("width", +percent + "%");
        $(".progress .progress-bar .status").text(+percent + "%");
    };

    var add_uploaded_file_to_list = function (file) {
        var list_group = $('.list-group');
        var file_item = "<a href=\"/view/" + file.name + "\" class=\"list-group-item list-group-item-success\"><span class=\"badge alert-success pull-right\">Success</span>" + file.name + "</a>";
        list_group.append(file_item);
    };

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

    var startUpload = function (file) {
        // reset progress bar
        $(".progress .progress-bar").css("width", "0%");
        $(".progress .progress-bar .status").text("0%");

        var formData = new FormData();
        formData.append("files", file);
        $.ajax({
            type: "POST",
            url: host_domain_url + "upload",
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    myXhr.upload.addEventListener('progress', progressHandling, false);
                }
                return myXhr;
            },
            success: function (data) {
                add_uploaded_file_to_list(file);
            },
            error: function (error) {
                add_alert(error.responseJSON.message);
            },
            async: true,
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            timeout: 60000

        });
    };

    uploadForm.addEventListener('submit', function (e) {
        var uploadFiles = document.getElementById('js-upload-files').files;
        e.preventDefault();

        for (var i = 0; i < uploadFiles.length; i++) {
            startUpload(uploadFiles[i]);
        }
    });

    dropZone.ondrop = function (e) {
        e.preventDefault();
        this.className = 'upload-drop-zone';

        var uploadFiles = e.dataTransfer.files;
        for (var i = 0; i < uploadFiles.length; i++) {
            startUpload(uploadFiles[i]);
        }
    };

    dropZone.ondragover = function () {
        this.className = 'upload-drop-zone drop';
        return false;
    };

    dropZone.ondragleave = function () {
        this.className = 'upload-drop-zone';
        return false;
    };

});