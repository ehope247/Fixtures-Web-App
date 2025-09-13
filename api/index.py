# api/index.py (Final Version with Smart Throttle)

from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
import json
import time

app = Flask(__name__, template_folder='../public', static_folder='../public')

# --- Securely Load API Keys from Vercel ---
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# --- API URLs ---
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"
TAVILY_API_URL = "https://api.tavily.com/search"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- The Cache (Still important for performance) ---
api_cache = {}
CACHE_DURATION_SECONDS = 3600 # Cache results for 1 hour

# --- Main Route ---
@app.route('/')
def home():
    return render_template('index.html')

# --- API Endpoints (These are unchanged) ---
@app.route('/api/competitions')
def get_competitions():
    if not FOOTBALL_API_KEY: return jsonify({"error": "Football API key not configured"}), 500
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions", headers=headers)
        response.raise_for_status()
        data = response.json().get('competitions', [])
        return jsonify(data)
    except requests.exceptions.RequestException as e: return jsonify({"error": str(e)}), 500

@app.route('/api/fixtures')
def get_fixtures():
    competition_id = request.args.get('id')
    if not competition_id: return jsonify({"error": "Competition ID is required"}), 400
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    date_from, date_to = datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    params = {'dateFrom': date_from, 'dateTo': date_to, 'status': 'SCHEDULED'}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions/{competition_id}/matches", headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('matches', [])
        return jsonify(data)
    except requests.exceptions.RequestException as e: return jsonify({"error": str(e)}), 500

@app.route('/api/details')
def get_details():
    match_id = request.args.get('id')
    if not match_id: return jsonify({"error": "Match ID is required"}), 400
    current_time = time.time()
    if match_id in api_cache:
        cached_item = api_cache[match_id]
        if current_time - cached_item['timestamp'] < CACHE_DURATION_SECONDS:
            print(f"CACHE HIT for match {match_id}")
            return jsonify(cached_item['data'])
    print(f"CACHE MISS for match {match_id}")
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
    
    # --- SMART THROTTLE IN ACTION ---
    # The two AI calls are now made one after the other, with a delay.
    prediction = get_gemini_prediction(match_data, standings_data)
    news_summary = get_news_summary(match_data)

    final_data = {"prediction": prediction, "newsSummary": news_summary}
    api_cache[match_id] = {'timestamp': current_time, 'data': final_data}
    return jsonify(final_data)

# --- Helper Functions ---
def call_gemini(prompt):
    # --- THIS IS THE SMART THROTTLE ---
    print("Waiting for 2 seconds to respect API rate limits...")
    time.sleep(2) # Add a 2-second delay before every single call

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=45)
        response.raise_for_status()
        response_json = response.json()
        candidates = response_json.get('candidates')
        if not candidates: return "AI response blocked or empty. Potentially due to safety filters."
        content = candidates[0].get('content', {}).get('parts', [{}])[0].get('text')
        return content or "AI returned an empty response."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Gemini API Error: Rate limit exceeded.")
            # --- THIS IS THE NEW, PROFESSIONAL ERROR MESSAGE ---
            return "The AI is currently busy due to high demand. Please try again in 60 seconds."
        print(f"Gemini Call Error: {e}")
        return "AI analysis could not be completed at this time."
    except Exception as e:
        print(f"Gemini Call Error: {e}")
        return "AI analysis could not be completed at this time."

def get_gemini_prediction(match_data, standings=None):
    # This function is now cleaner as the delay is handled by call_gemini
    home_team_name, away_team_name = match_data.get('homeTeam', {}).get('name', 'Home'), match_data.get('awayTeam', {}).get('name', 'Away')
    prompt = (f"You are a world-class football analyst. Provide a concise, expert analysis for the match between {home_team_name} and {away_team_name}.\n\n")
    if standings and standings.get('standings'):
        home_stats = away_stats = None
        for team in standings['standings'][0].get('table', []):
            if team['team']['id'] == match_data['homeTeam']['id']: home_stats = team
            if team['team']['id'] == match_data['awayTeam']['id']: away_stats = team
        if home_stats and away_stats:
            home_form, away_form = (f.replace(',', ' ') if f else 'N/A' for f in [home_stats.get('form'), away_stats.get('form')])
            prompt += (f"**Data Analysis:**\n- **{home_stats['team']['name']}**: Position {home_stats['position']}, Points: {home_stats['points']}, Form: {home_form}, GF: {home_stats['goalsFor']}, GA: {home_stats['goalsAgainst']}.\n- **{away_stats['team']['name']}**: Position {away_stats['position']}, Points: {away_stats['points']}, Form: {away_form}, GF: {away_stats['goalsFor']}, GA: {away_stats['goalsAgainst']}.\n\nBased on this data, analyze their form, attacking threat, and defensive stability. ")
    else:
        prompt += "Based on general knowledge of the teams, analyze their matchup. "
    prompt += ("Conclude with three separate prediction lines in this exact format:\nPrediction: [Home Win/Draw/Away Win]\nCorrect Score: [e.g., 2-1]\nOver/Under 2.5 Goals: [Over/Under]")
    return call_gemini(prompt)

def get_tavily_news(query):
    # This function is unchanged
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}
    payload = json.dumps({"query": query, "search_depth": "basic", "include_raw_content": True, "max_results": 3})
    try:
        response = requests.post(TAVILY_API_URL, data=payload, headers=headers)
        response.raise_for_status()
        return response.json().get('results', [])
    except Exception as e:
        print(f"Tavily Error: {e}")
        return []

def get_news_summary(match_data):
    # This function now calls the throttled call_gemini function
    home_team, away_team = match_data.get('homeTeam', {}).get('name', ''), match_data.get('awayTeam', {}).get('name', '')
    articles = get_tavily_news(f"latest football team news and player injuries for {home_team} and {away_team}")
    if not articles: return "No recent news found."
    raw_content = ""
    for article in articles:
        raw_content += f"Article Title: {article.get('title')}\nContent: {article.get('raw_content', '')}\n\n"
    prompt = (f"You are an intelligence analyst. Read the following news articles. Provide a short, bulleted summary of key information, such as player injuries, team morale, or recent news. Do not make up information.\n\nARTICLES:\n{raw_content}")
    return call_gemini(prompt)