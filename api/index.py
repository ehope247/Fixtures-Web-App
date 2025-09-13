# api/index.py (Final Slim Version)
from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
import joblib

app = Flask(__name__, template_folder='../public', static_folder='../public')
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
try:
    # We need to specify the full path for Vercel
    model = joblib.load('prediction_model.joblib')
except FileNotFoundError:
    model = None
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"

@app.route('/')
def home(): return render_template('index.html')
@app.route('/api/competitions')
def get_competitions():
    if not FOOTBALL_API_KEY: return jsonify({"error": "API key not configured"}), 500
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions", headers=headers)
        response.raise_for_status()
        return jsonify(response.json().get('competitions', []))
    except Exception as e: return jsonify({"error": str(e)}), 500
@app.route('/api/fixtures')
def get_fixtures():
    comp_id = request.args.get('id')
    if not comp_id: return jsonify({"error": "Competition ID required"}), 400
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    date_from = datetime.now().strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    params = {'dateFrom': date_from, 'dateTo': date_to, 'status': 'SCHEDULED'}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions/{comp_id}/matches", headers=headers, params=params)
        response.raise_for_status()
        return jsonify(response.json().get('matches', []))
    except Exception as e: return jsonify({"error": str(e)}), 500
@app.route('/api/details')
def get_details():
    home_id = request.args.get('home_id')
    away_id = request.args.get('away_id')
    if not home_id or not away_id: return jsonify({"error": "Team IDs required"}), 400
    if not model: return jsonify({"prediction": "Model not available."})
    try:
        input_data = [[int(home_id), int(away_id)]]
        prediction_code = model.predict(input_data)[0]
        result_map = {0: "Home Team Win", 1: "Away Team Win", 2: "Draw"}
        prediction_text = result_map.get(prediction_code, "Prediction undetermined.")
        return jsonify({"prediction": prediction_text, "newsSummary": "This statistical model does not use news analysis."})
    except Exception as e: return jsonify({"error": f"Prediction failed: {e}"}), 500