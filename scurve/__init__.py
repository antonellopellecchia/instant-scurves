from flask import Flask, render_template, request, jsonify

from scurve import daq

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # main configuration interface
    @app.route("/")
    def index():
        return render_template("index.html")

    # scurve result
    @app.route("/result")
    def scurve_result():

        block, oh = request.args.get("block"), request.args.get("oh")
        vfats = list(range(12))

        # launch first the scurve
        if not daq.running:
            daq.launch_scurve(block, oh, vfats)

        return render_template("scurve.html", oh=oh)

    @app.route("/api")
    def api():
        daq_status = {
            "running": daq.running,
            "saving": daq.saving
        }
        variable = request.args.get("get")
        return jsonify({
            "value": daq_status[variable]
        })
 
    return app