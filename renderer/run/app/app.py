import os
import sys
from flask import Flask, render_template, jsonify, request
import json

# Make sure Python can find your modules (assuming they're in the same directory or a subfolder)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from correction_service import get_correction_explanation
from generate_explanation import generate_correction_explanation_single  # <--- Use correct file name

app = Flask(__name__)

@app.route("/")
def index():
    """
    Serves the main frontend page.
    """
    return render_template("index.html")

@app.route("/data.json")
def get_data():
    """
    Fetches and serves sentence/correction data from 'output.json' (adjust path as needed).
    """
    try:
        with open("output.json", "r") as f:  # Ensure 'output.json' is in the right location
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Failed to load output.json", "details": str(e)}), 500

@app.route("/highlight_click", methods=["POST"])
def highlight_click():
    """
    Handles highlight-box clicks from the frontend. 
    Calls `get_correction_explanation` to retrieve the relevant sentence/block data,
    then runs a multi-step LLM explanation via `generate_correction_explanation_single`.
    """
    try:
        # 1) Parse the incoming JSON payload (blockType, blockIndex, sentenceIndex)
        data = request.get_json()
        print("[DEBUG] Received highlight click:", data)

        # 2) Retrieve correction details (sentence/block) from JSON metadata
        correction_info = get_correction_explanation(data)
        print("[DEBUG] Correction result:", correction_info)

        # 3) If there's an error (e.g. block not found), send it back
        if "error" in correction_info:
            return jsonify(correction_info), 400

        # 4) Extract fields for the explanation function
        block_type = data.get("blockType")
        ocr_sentence = correction_info.get("ocr_sentence")
        corrected_sentence = correction_info.get("corrected_sentence")
        correction_block = correction_info.get("correction_block")

        # 5) Generate explanation using the multi-step approach
        explanation = generate_correction_explanation_single(
            block_type, ocr_sentence, corrected_sentence, correction_block
        )
        result = {"explanation": explanation}
        

        # 6) Return the explanation as JSON
        return jsonify(result)
    except Exception as e:
        print("[ERROR] Failed to process highlight click:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    """
    Runs the Flask app (development mode).
    In production, use a WSGI server (e.g. Gunicorn) instead:
      gunicorn -b 0.0.0.0:5000 app:app
    """
    app.run(debug=True, host="0.0.0.0", port=5000)
