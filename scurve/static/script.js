setInterval(function() {

    /* What to do every second:
     * chack whether an scurve is running,
     * show or hide the stop button,
     * update the scurve picture
     */
    var runningFlag = $("#flag_running");
    var stopButton = $("#button_stop");

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
            stopButton.hide();
        }
    });
}, 1000);

$(function() {

    // start new scurve:
    $("#button_start").click(function() {
        var block = $("#scurve_block").val();
        var oh = $("#scurve_oh").val();
        console.log("Sending block " + block + " and OH " + oh);
        $.getJSON(
            "/api?action=start",
            {"block": block, "oh": oh },
            function(data) {
                console.log("Starting action response: " + data["status"]);
                $("#content_new").hide();
                $("#content_scurve").show();
            }
        );
    });

    // stop ongoing scurve:
    $("#button_stop").click(function() {
        $.getJSON("/api?action=stop", function(data) {
            console.log("Stopping action response: " + data["status"]);
        });
    });
});

