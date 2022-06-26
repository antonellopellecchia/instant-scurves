setInterval(function() {

    /* What to do every second:
     * chack whether an scurve is running,
     * show or hide the stop button,
     * update the scurve picture
     */
    var runningFlag = $("#flag_running");
    var stopButton = $("#button_stop");
    var newButton = $("#button_new");

    var scurveImage = $("#scurve_img");
    var scurveSrcBase = scurveImage.attr("src").split("?")[0];
    var isSaving = true;
    var isRunning = false;

    $.getJSON("/api?get=running", function(data) {
        isRunning = data["value"];
        if (isRunning) {
            // set the indicator as running, show stop button:
            runningFlag.text("Running");
            stopButton.show();

            // update the figure only if it is not being saved:
            $.getJSON("/api?get=saving", function(data) {
                isSaving = data["value"];
                console.log("Running status: " + isRunning + ", saving status: " + isSaving);
                if (!isSaving) scurveImage.attr("src", scurveSrcBase+"?"+new Date().getTime());
            });
        } else {
            runningFlag.text("Idle");
            // if we were running before, hide stop button and show new button:
            if (stopButton.css("display")!="none") {
                stopButton.hide();
                newButton.show();
            }
        }
    });
}, 1000);

$(function() {
   
    var showResult = function(data) {
        console.log("Starting action response: " + data["status"]);
        $("#content_new").hide();
        $("#content_scurve").show();
    }
    // if when the page loads an scurve is running, show the result:
    $.getJSON("/api?get=running", function(data) {
        if (data["value"]) showResult(data);
    });

    // start new scurve:
    $("#button_start").click(function() {
        var block = $("#scurve_block").val();
        var oh = $("#scurve_oh").val();
        console.log("Sending block " + block + " and OH " + oh);
        $.getJSON(
            "/api?action=start",
            {"block": block, "oh": oh },
            showResult
        );
    });

    // stop ongoing scurve:
    $("#button_stop").click(function() {
        $.getJSON("/api?action=stop", function(data) {
            console.log("Stopping action response: " + data["status"]);
            $("#button_stop").hide();
            $("#button_new").show();
        });
    });

    $("#button_new").click(function() {
        $("#button_new").hide();
        $("#content_new").show();
        $("#content_scurve").hide();
    });
});

