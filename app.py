import os
import json
import tempfile
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from crew import run_crew

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max upload


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files accepted"}), 400

    # Save to a temp file so crew.py can read it from disk
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
        file.save(tmp)
        tmp_path = tmp.name

    try:
        result = run_crew(tmp_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp_path)  # always clean up temp file

    return jsonify({
        "total_transactions": result["heuristics"]["total_transactions"],
        "flagged_count": result["heuristics"]["flagged_count"],
        "analyst": result["analyst"],
        "explainer": result["explainer"],
        "redteam": result["redteam"]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
