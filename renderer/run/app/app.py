from flask import Flask, render_template, jsonify
import json 

app = Flask(__name__, template_folder="/home/keithuncouth/hw_hero/renderer/run/templates")

@app.route("/")
def index():
    """
    Serve index.html to render corrections dynamically.
    """
    return render_template("index.html")

@app.route("/data.json")
def get_data():
    """
    Serve JSON data for sentences and corrections.
    Ensure this matches your actual backend JSON structure.
    """
    with open("output.json", "r") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
