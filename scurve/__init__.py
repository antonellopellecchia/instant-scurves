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


        return render_template("scurve.html", oh=oh)

    @app.route("/api")
    def api():
        daq_status = {
            "running": daq.running,
            "saving": daq.saving,
            "stopping": daq.stopping
        }
        variable = request.args.get("get")
        action = request.args.get("action")
        if variable:
            return jsonify({"value": daq_status[variable]})
        elif action:
            if action == "start":
                block, oh = request.args.get("block"), request.args.get("oh", type=int)
                if block == "ge21": vfats = list(range(12))
                elif block == "me0": vfats = [5,6,7,13,14,22,23]
                # launch the scurve
                if not daq.running:
                    daq.launch_scurve(block, oh, vfats)
                return jsonify({"status": "ok"})
            elif action == "stop":
                daq.stop()
                return jsonify({"status": "ok"})
 
    return app
