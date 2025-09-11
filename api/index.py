# api/index.py

from flask import Flask, render_template
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__, template_folder='../', static_folder='../')

# --- CONFIGURATION ---
# IMPORTANT: We will add your API Key here later using Vercel's secure secrets.
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "YOUR_FALLBACK_API_KEY")
API_URL = "https://api.football-data.org/v4/competitions/PL/matches"

# --- TRIAL LOGIC ---
# This sets the site to expire ON 2025-08-15.
# The launch date is automatically set to 3 days before the expiration.
EXPIRATION_DATE = datetime(2025, 9, 15)

@app.route('/')
def home():
    # Get today's date
    today = datetime.now()

    # Check if the trial has expired
    if today > EXPIRATION_DATE:
        # If expired, show a simple "locked" message
        return "<h2>The free trial for this service has expired.</h2>", 403

    # If trial is active, proceed to fetch data
    try:
        headers = {'X-Auth-Token': API_KEY}
        
        # Define the date range: today for the next 3 days
        date_from = today.strftime('%Y-%-m-%d')
        date_to = (today + timedelta(days=3)).strftime('%Y-%m-%d')
        
        params = {
            'dateFrom': date_from,
            'dateTo': date_to,
            'status': 'SCHEDULED'
        }

        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)
        
        data = response.json()
        fixtures = data.get('matches', [])

        # Group fixtures by date
        grouped_fixtures = {}
        for fixture in fixtures:
            # Extract the date part (YYYY-MM-DD) from the full UTC datetime string
            match_date_str = fixture['utcDate'].split('T')[0]
            if match_date_str not in grouped_fixtures:
                grouped_fixtures[match_date_str] = []
            
            # Extract and format time
            match_time = fixture['utcDate'].split('T')[1].replace('Z', '')[:5]
            fixture['matchTime'] = match_time
            
            grouped_fixtures[match_date_str].append(fixture)
        
        # Pass the grouped data to our HTML template
        return render_template('index.html', all_fixtures=grouped_fixtures)

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        # Show a user-friendly error message on the website
        return "<h2>Sorry, could not load fixture data at this time. Please try again later.</h2>", 500

# This line allows Vercel to run the Flask app.
# It's a standard requirement for this setup.
if __name__ == "__main__":
    app.run(debug=True)