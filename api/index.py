# api/index.py (Final Version with Professional Error Handling)

from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
import json
import time

app = Flask(__name__, template_folder='../public', static_folder='../public')

# Securely Load API Keys from Vercel
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# API URLs
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"
TAVILY_API_URL = "https://api.tavily.com/search"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

api_cache = {}
CACHE_DURATION_SECONDS = 7200

# Main Route
@app.route('/')
def home():
    return render_template('index.html')

# --- API Endpoints ---
@app.route('/api/competitions')
def get_competitions():
    if not FOOTBALL_API_KEY:
        return jsonify({"error": "API key is not configured on the server."}), 500
    
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions", headers=headers, timeout=10)
        response.raise_for_status()
        
        competitions = response.json().get('competitions', [])
        
        if not competitions:
            return jsonify({"error": "The live data provider (football-data.org) is not providing any competitions on the free tier at this moment."}), 404
        
        return jsonify(competitions)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not connect to the live data provider. Error: {e}"}), 503

@app.route('/api/fixtures')
def get_fixtures():
    comp_id = request.args.get('id')
    if not comp_id: return jsonify({"error": "ID required"}), 400
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    d_from, d_to = datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    params = {'dateFrom': d_from, 'dateTo': d_to, 'status': 'SCHEDULED'}
    try:
        r = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions/{comp_id}/matches", headers=headers, params=params)
        r.raise_for_status(); return jsonify(r.json().get('matches', []))
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/details')
def get_details():
    match_id = request.args.get('id')
    if not match_id: return jsonify({"error": "ID required"}), 400
    now = time.time()
    if match_id in api_cache and now - api_cache[match_id]['ts'] < CACHE_DURATION_SECONDS:
        print(f"CACHE HIT: {match_id}"); return jsonify(api_cache[match_id]['data'])
    print(f"CACHE MISS: {match_id}")
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        match_res = requests.get(f"{FOOTBALL_API_BASE_URL}/matches/{match_id}", headers=headers)
        match_res.raise_for_status(); match_data = match_res.json()
        comp_id = match_data.get('competition', {}).get('id')
        standings_res = requests.get(f"{FOOTBALL_API_BASE_URL}/competitions/{comp_id}/standings", headers=headers)
        standings_data = standings_res.json() if standings_res.ok else None
    except Exception as e: return jsonify({"error": f"Match data fetch failed: {e}"}), 500
    
    final_data = get_ai_analysis(match_data, standings_data)
    api_cache[match_id] = {'ts': now, 'data': final_data}
    return jsonify(final_data)

# Helper Functions
def call_gemini(prompt):
    print("THROTTLE: Waiting 3 seconds before AI call...")
    time.sleep(3)
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=45)
        response.raise_for_status()
        res_json = response.json()
        candidates = res_json.get('candidates')
        if not candidates: return "AI response blocked (Safety)."
        content = candidates[0].get('content', {}).get('parts', [{}])[0].get('text')
        return content or "AI returned empty response."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return "AI is busy (Rate Limit). Please try again in a moment."
        return f"AI analysis failed: HTTP Error {e.response.status_code}"
    except Exception as e: return f"AI analysis failed: {e}"

def get_tavily_news_content(query):
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
    payload = json.dumps({"query": query, "search_depth": "basic", "include_raw_content": True, "max_results": 3})
    try:
        r = requests.post(TAVILY_API_URL, data=payload, headers=headers)
        r.raise_for_status(); results = r.json().get('results', [])
        return "\n".join([f"Article: {res.get('title')}\nContent: {res.get('raw_content', '')}" for res in results])
    except Exception as e: print(f"Tavily Error: {e}"); return ""

def get_ai_analysis(match_data, standings=None):
    home_name, away_name = match_data.get('homeTeam', {}).get('name', 'Home'), match_data.get('awayTeam', {}).get('name', 'Away')
    news_content = get_tavily_news_content(f"latest football team news, player injuries for {home_name} and {away_name}")
    prompt = (f"You are a world-class football analyst. First, read the provided team data and recent news articles. Then, provide a complete, expert analysis for the match between {home_name} and {away_name}.\n\n")
    if standings and standings.get('standings'):
        home_stats = away_stats = None
        for team in standings['standings'][0].get('table', []):
            if team['team']['id'] == match_data['homeTeam']['id']: home_stats = team
            if team['team']['id'] == match_data['awayTeam']['id']: away_stats = team
        if home_stats and away_stats:
            home_form, away_form = (f.replace(',', ' ') if f else 'N/A' for f in [home_stats.get('form'), away_stats.get('form')])
            prompt += (f"**DATA ANALYSIS:**\n- **{home_stats['team']['name']}**: Pos {home_stats['position']}, Pts: {home_stats['points']}, Form: {home_form}\n- **{away_stats['team']['name']}**: Pos {away_stats['position']}, Pts: {away_stats['points']}, Form: {away_form}\n\n")
    if news_content: prompt += f"**LATEST NEWS CONTENT:**\n{news_content}\n\n"
    prompt += ("**FINAL OUTPUT:**\nBased on all available data and news, provide your final analysis in two parts. First, a single paragraph of expert analysis that includes key news. Second, conclude with three separate prediction lines in this exact format:\nPrediction: [Home Win/Draw/Away Win]\nCorrect Score: [e.g., 2-1]\nOver/Under 2.5 Goals: [Over/Under]")
    full_analysis = call_gemini(prompt)
    try:
        prediction_index = full_analysis.lower().find('prediction:')
        if prediction_index != -1:
            analysis_text, prediction_lines = full_analysis[:prediction_index].strip(), full_analysis[prediction_index:].strip()
            news_summary = "Key news and injuries are integrated into the main analysis above."
            final_prediction = f"{analysis_text}\n\n{prediction_lines}"
        else:
            final_prediction, news_summary = full_analysis, "Could not be separated from analysis."
    except:
        final_prediction, news_summary = full_analysis, "Could not be separated from analysis."
    return {"prediction": final_prediction, "newsSummary": news_summary}