from flask import Flask, render_template, jsonify, request
import json 

app = Flask(__name__)

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
    """
    with open("output.json", "r") as f:
        data = json.load(f)
    return jsonify(data)

# Add this new endpoint for handling highlight clicks.
@app.route("/highlight_click", methods=["POST"])
def highlight_click():
    data = request.get_json()  # Get JSON payload from the POST request
    print("Received highlight click:", data)  # For debugging in the console
    # Respond with a JSON message confirming receipt.
    return jsonify({"status": "success", "received": data})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
