# train_model.py (Original scikit-learn Version)
import requests
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
import os

print("Starting the model training process...")
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
if not API_KEY:
    print("FATAL ERROR: FOOTBALL_DATA_API_KEY is not set in Replit Secrets.")
    exit()
API_URL = "https://api.football-data.org/v4/competitions/PL/matches?season=2023"
headers = {'X-Auth-Token': API_KEY}
try:
    print("Downloading historical match data...")
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()
    data = response.json()['matches']
    print(f"Successfully downloaded data for {len(data)} matches.")
except Exception as e:
    print(f"Failed to download data: {e}"); exit()
prepared_data = []
for match in data:
    if match['status'] == 'FINISHED':
        prepared_data.append({
            'home_team_id': match['homeTeam']['id'],
            'away_team_id': match['awayTeam']['id'],
            'winner': 0 if match['score']['winner'] == 'HOME_TEAM' else 1 if match['score']['winner'] == 'AWAY_TEAM' else 2
        })
df = pd.DataFrame(prepared_data)
X = df[['home_team_id', 'away_team_id']]
y = df['winner']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LogisticRegression()
print("Training the AI model...")
model.fit(X_train, y_train)
print("Model training complete.")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model Accuracy on test data: {accuracy * 100:.2f}%")
model_filename = 'prediction_model.joblib'
joblib.dump(model, model_filename)
print(f"Model successfully saved to '{model_filename}'")