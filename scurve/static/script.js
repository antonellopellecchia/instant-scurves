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
                console.log("Running status: " + isRunning + ", saving status: " + data["value"]);
                isSaving = data["value"];
            });
            if (!isSaving) scurveImage.attr("src", scurveSrcBase+"?"+new Date().getTime());
        } else {
            runningFlag.text("Idle");
            stopButton.hide();
        }
    });
}, 1000);

$(function() {
    $("#button_stop").click(function() {
        $.getJSON("/api?action=stop", function(data) {
            console.log("Stopping action response: " + data["status"]);
        });
    });
});

