# api/index.py (Final Version with Your Own Model)

from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
import joblib

app = Flask(__name__, template_folder='../public', static_folder='../public')

# --- Securely Load API Keys from Vercel ---
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")

# --- Load Your Trained Prediction Model ---
try:
    model = joblib.load('prediction_model.joblib')
    print("Prediction model loaded successfully.")
except FileNotFoundError:
    model = None
    print("ERROR: prediction_model.joblib not found. Did you run the training script?")

# --- API URL ---
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"

# --- Main Route: Serves the website itself ---
@app.route('/')
def home():
    return render_template('index.html')

# --- API Endpoint 1: Get all competitions ---
@app.route('/api/competitions')
def get_competitions():
    if not FOOTBALL_API_KEY: return jsonify({"error": "Football API key is not configured"}), 500
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions", headers=headers)
        response.raise_for_status()
        data = response.json().get('competitions', [])
        return jsonify(data)
    except requests.exceptions.RequestException as e: return jsonify({"error": str(e)}), 500

# --- API Endpoint 2: Get fixtures for a specific competition ---
@app.route('/api/fixtures')
def get_fixtures():
    competition_id = request.args.get('id')
    if not competition_id: return jsonify({"error": "Competition ID is required"}), 400
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    date_from = datetime.now().strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    params = {'dateFrom': date_from, 'dateTo': date_to, 'status': 'SCHEDULED'}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions/{competition_id}/matches", headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('matches', [])
        return jsonify(data)
    except requests.exceptions.RequestException as e: return jsonify({"error": str(e)}), 500

# --- API Endpoint 3: Get details (Your Model's Prediction) for a specific match ---
@app.route('/api/details')
def get_details():
    home_team_id = request.args.get('home_id')
    away_team_id = request.args.get('away_id')

    if not home_team_id or not away_team_id:
        return jsonify({"error": "Team IDs are required"}), 400
    
    if not model:
        return jsonify({"prediction": "Prediction model is not available."})

    try:
        # Prepare the data for the model
        input_data = [[int(home_team_id), int(away_team_id)]]
        
        # Use your model to make a prediction
        prediction_code = model.predict(input_data)[0]

        # Convert the prediction code to a human-readable result
        result_map = {0: "Home Team Win", 1: "Away Team Win", 2: "Draw"}
        prediction_text = result_map.get(prediction_code, "Prediction could not be determined.")

        # For this version, news is no longer a feature
        news_summary = "News analysis has been replaced by our new statistical prediction engine."

        return jsonify({
            "prediction": prediction_text,
            "newsSummary": news_summary
        })
    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({"error": "Failed to generate a prediction."}), 500