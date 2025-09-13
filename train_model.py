# train_model.py

import requests
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
import os

print("Starting the model training process...")

# --- Step 1: Get Historical Data ---
# We will use the Football API to get all matches from last season's Premier League.

API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
if not API_KEY:
    print("FATAL ERROR: FOOTBALL_DATA_API_KEY is not set in your Replit Secrets.")
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
    print(f"Failed to download data: {e}")
    exit()

# --- Step 2: Prepare the Data for Learning ---
# We need to convert the raw data into a simple format the AI can understand.

prepared_data = []
for match in data:
    if match['status'] == 'FINISHED':
        prepared_data.append({
            'home_team_id': match['homeTeam']['id'],
            'away_team_id': match['awayTeam']['id'],
            'winner': 0 if match['score']['winner'] == 'HOME_TEAM' else 1 if match['score']['winner'] == 'AWAY_TEAM' else 2 # 0=Home, 1=Away, 2=Draw
        })

df = pd.DataFrame(prepared_data)
print("Data prepared for training. Example:")
print(df.head())

# --- Step 3: Train the Prediction Model ---
# We will use the data to teach a simple AI model to recognize patterns.

# Define our features (the inputs) and the target (what we want to predict)
X = df[['home_team_id', 'away_team_id']]
y = df['winner']

# Split the data so we can test our model's accuracy
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train the model
model = LogisticRegression()
print("Training the AI model...")
model.fit(X_train, y_train)
print("Model training complete.")

# --- Step 4: Test the Model ---
# Let's see how accurate our new model is.
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model Accuracy on test data: {accuracy * 100:.2f}%")

# --- Step 5: Save the "Brain" to a File ---
# We will save our trained model to a file so our website can use it later.
model_filename = 'prediction_model.joblib'
joblib.dump(model, model_filename)
print(f"Model successfully saved to '{model_filename}'")
print("You can now run the main web application.")