from flask import Flask, jsonify

app = Flask(__name__)
latest_data = {}

@app.route("/")
def home():
    return jsonify(latest_data)

def update_dashboard(report, times):
    global latest_data
    latest_data = {
        "report": report,
        "times": times
    }

def run_dashboard():
    app.run(host="0.0.0.0", port=5000)