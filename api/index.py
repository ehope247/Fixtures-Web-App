# api/index.py (Upgraded to a full API Backend)

from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__, template_folder='../', static_folder='../')

# --- Securely Load API Keys from Vercel ---
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# --- API URLs ---
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"
TAVILY_API_URL = "https://api.tavily.com/search"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- Main Route: Serves the website itself ---
@app.route('/')
def home():
    # This just serves the main HTML page.
    # The JavaScript on that page will then fetch the data.
    return render_template('index.html')

# --- API Endpoint 1: Get all competitions ---
@app.route('/api/competitions')
def get_competitions():
    if not FOOTBALL_API_KEY:
        return jsonify({"error": "Football API key is not configured"}), 500
    
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions", headers=headers)
        response.raise_for_status()
        data = response.json().get('competitions', [])
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# --- API Endpoint 2: Get fixtures for a specific competition ---
@app.route('/api/fixtures')
def get_fixtures():
    competition_id = request.args.get('id')
    if not competition_id:
        return jsonify({"error": "Competition ID is required"}), 400

    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    date_from = datetime.now().strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    params = {'dateFrom': date_from, 'dateTo': date_to, 'status': 'SCHEDULED'}

    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions/{competition_id}/matches", headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('matches', [])
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# --- API Endpoint 3: Get details (AI Prediction & News) for a specific match ---
@app.route('/api/details')
def get_details():
    match_id = request.args.get('id')
    if not match_id:
        return jsonify({"error": "Match ID is required"}), 400

    # 1. Get Match and Standings Data
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        match_response = requests.get(f"{FOOTBALL_API_BASE_URL}/matches/{match_id}", headers=headers)
        match_response.raise_for_status()
        match_data = match_response.json()
        
        comp_id = match_data.get('competition', {}).get('id')
        standings_response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions/{comp_id}/standings", headers=headers)
        standings_data = standings_response.json() if standings_response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to get match data: {e}"}), 500

    # 2. Get AI Prediction
    prediction = get_gemini_prediction(match_data, standings_data)

    # 3. Get News
    home_team = match_data.get('homeTeam', {}).get('name', '')
    away_team = match_data.get('awayTeam', {}).get('name', '')
    news = get_tavily_news(f"latest football news {home_team} and {away_team}")
    
    return jsonify({
        "prediction": prediction,
        "news": news
    })

# --- Helper function for Gemini AI ---
def get_gemini_prediction(match_data, standings=None):
    # This is the same reliable function from our bot
    home_team_name = match_data.get('homeTeam', {}).get('name', 'Home Team')
    away_team_name = match_data.get('awayTeam', {}).get('name', 'Away Team')
    prompt = (f"You are an expert football analyst. Provide a concise analysis for the match between {home_team_name} and {away_team_name}.\n\n")
    # ... (rest of the prompt logic) ...
    if standings and standings.get('standings'):
        # ... logic to add standings to prompt ...
        pass # Placeholder for brevity
    prompt += ("Conclude with three separate lines:\nPrediction: [Home Win/Draw/Away Win]\nCorrect Score: [e.g., 2-1]\nOver/Under 2.5 Goals: [Over/Under]")
    
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        response_json = response.json()
        content = response_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
        return content or "AI returned an empty response."
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "AI analysis could not be completed."

# --- Helper function for Tavily News ---
def get_tavily_news(query):
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}
    payload = json.dumps({"query": query, "search_depth": "basic", "max_results": 3})
    try:
        response = requests.post(TAVILY_API_URL, data=payload, headers=headers)
        response.raise_for_status()
        return response.json().get('results', [])
    except Exception as e:
        print(f"Tavily Error: {e}")
        return []