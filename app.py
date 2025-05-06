import streamlit as st
import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from preprocessing import generate_features

# ----------------------------
# Cache data loading
# ----------------------------
@st.cache_data
def load_data():
    return pd.read_excel("data.xlsx")

data = load_data()

# ----------------------------
# Load models and scalers (only once!)
# ----------------------------
with open("logistic_regression_model.pkl", "rb") as f:
    winner_model = pickle.load(f)

with open("scaler.pkl", "rb") as f:
    winner_scaler = pickle.load(f)

with open("btts_log_model.pkl", "rb") as f:
    btts_model = pickle.load(f)

with open("btts_scaler.pkl", "rb") as f:
    btts_scaler = pickle.load(f)

over_thresholds = [1.5, 2.5, 3.5, 4.5]
over_models = {}
over_scalers = {}

for t in over_thresholds:
    with open(f"log_total_over_{t}_model.pkl", "rb") as f:
        over_models[t] = pickle.load(f)
    with open(f"log_total_over_{t}_scaler.pkl", "rb") as f:
        over_scalers[t] = pickle.load(f)

# ----------------------------
# FIFA Teams and Tournaments
# ----------------------------
fifa_teams = sorted([team for team in data['home_team'].unique() if pd.notna(team)])

tournaments = [
    "UEFA Euro", "Copa America", "FIFA World Cup", "FIFA World Cup qualification",
    "Gold Cup", "AFC Asian Cup", "African Cup of Nations", "Confederations Cup",
    "UEFA Euro qualification", "UEFA Nations League", "Other"
]

# ----------------------------
# Sidebar Inputs
# ----------------------------
st.title("Football Match Outcome Predictor")

st.sidebar.header("Match Details")

home_team = st.sidebar.selectbox("Home Team", fifa_teams)
away_team = st.sidebar.selectbox("Away Team", fifa_teams)
tournament = st.sidebar.selectbox("Tournament", tournaments)
match_country = st.sidebar.selectbox("Match Country", fifa_teams)

home_odds = st.sidebar.number_input("Home Odds", value=2.0)
draw_odds = st.sidebar.number_input("Draw Odds", value=3.0)
away_odds = st.sidebar.number_input("Away Odds", value=3.5)

match_date = st.sidebar.date_input("Match Date", value=datetime.today())

# ----------------------------
# Helper functions for insights
# ----------------------------
def get_latest_rank(team, date):
    ranks = data[(data['date'] <= date) & ((data['home_team'] == team) | (data['away_team'] == team))]
    ranks = ranks.sort_values(by='date', ascending=False)
    if not ranks.empty:
        return int(ranks.iloc[0]['home_rank'] if ranks.iloc[0]['home_team'] == team else ranks.iloc[0]['away_rank'])
    else:
        return "N/A"

def get_last_5_form(team, date):
    matches = data[((data['home_team'] == team) | (data['away_team'] == team)) & (data['date'] < date)].sort_values(by='date', ascending=False).head(5)
    form = []
    for _, row in matches.iterrows():
        if (row["winner"] == "home_team" and row["home_team"] == team) or (row["winner"] == "away_team" and row["away_team"] == team):
            form.append("W")
        elif row["winner"] == "draw":
            form.append("D")
        else:
            form.append("L")
    return " | ".join(reversed(form)) if not matches.empty else "No recent matches"

def get_last_5_goals(team, date):
    matches = data[((data['home_team'] == team) | (data['away_team'] == team)) & (data['date'] < date)].sort_values(by='date', ascending=False).head(5)
    scored = []
    conceded = []
    for _, row in matches.iterrows():
        if row['home_team'] == team:
            scored.append(str(row['home_score']))
            conceded.append(str(row['away_score']))
        else:
            scored.append(str(row['away_score']))
            conceded.append(str(row['home_score']))
    return (" | ".join(reversed(scored)), " | ".join(reversed(conceded))) if not matches.empty else ("No data", "No data")

def get_head_to_head(home_team, away_team, date):
    matches = data[
        (((data['home_team'] == home_team) & (data['away_team'] == away_team)) |
         ((data['home_team'] == away_team) & (data['away_team'] == home_team))) &
        (data['date'] < date)
    ].sort_values(by='date', ascending=False)
    if matches.empty:
        return ["No previous matches"]
    else:
        results = []
        for _, row in matches.iterrows():
            result = f"{row['date'].date()}: {row['home_team']} {row['home_score']} - {row['away_score']} {row['away_team']}"
            results.append(result)
        return results

# ----------------------------
# Prediction and Insights
# ----------------------------
if st.sidebar.button("Predict Outcome"):
    if home_team == away_team:
        st.error("Home and Away teams must be different.")
    else:
        X_new = generate_features(home_team, away_team, tournament, match_country,
                                  home_odds, draw_odds, away_odds, match_date, data)

        # Winner probabilities
        X_scaled = winner_scaler.transform(X_new)
        winner_proba = winner_model.predict_proba(X_scaled)[0]

        st.header("Predicted Probabilities (Match Winner)")
        st.write(f"Home Win: {winner_proba[0]*100:.2f}%")
        st.write(f"Draw: {winner_proba[1]*100:.2f}%")
        st.write(f"Away Win: {winner_proba[2]*100:.2f}%")

        # Value Bet
        probs = winner_proba
        odds = np.array([home_odds, draw_odds, away_odds])
        value_bets = probs * odds > 1.1

        st.header("Value Bet Suggestion")
        outcomes = ["Home Win", "Draw", "Away Win"]
        any_value_bet = False
        for idx, vb in enumerate(value_bets):
            if vb:
                value = probs[idx] * odds[idx]
                st.success(f"Value Bet: {outcomes[idx]} (Value: {value:.2f})")
                any_value_bet = True
        if not any_value_bet:
            st.warning("No Value Bet Found for this match.")


        # ----------------------------
        # BTTS Prediction
        # ----------------------------
        X_btts_scaled = btts_scaler.transform(X_new)
        btts_prob = btts_model.predict_proba(X_btts_scaled)[0][1]
        st.header("Both Teams to Score (BTTS)")
        st.write(f"Probability of BTTS: {btts_prob*100:.2f}%")

        # ----------------------------
        # Total Goals Predictions
        # ----------------------------
        st.header("Total Goals Probabilities")
        for t in over_thresholds:
            X_over_scaled = over_scalers[t].transform(X_new)
            over_prob = over_models[t].predict_proba(X_over_scaled)[0][1]
            st.write(f"Over {t}: {over_prob*100:.2f}%")

        # ----------------------------
        # Extra Match Insights
        # ----------------------------
        st.header("Match Insights")

        date_obj = pd.to_datetime(match_date)

        home_rank = get_latest_rank(home_team, date_obj)
        away_rank = get_latest_rank(away_team, date_obj)

        home_form = get_last_5_form(home_team, date_obj)
        away_form = get_last_5_form(away_team, date_obj)

        home_scored, home_conceded = get_last_5_goals(home_team, date_obj)
        away_scored, away_conceded = get_last_5_goals(away_team, date_obj)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"{home_team}")
            st.write(f"FIFA Rank: {home_rank}")
            st.write(f"Last 5 Form: {home_form}")
            st.write(f"Goals Scored: {home_scored}")
            st.write(f"Goals Conceded: {home_conceded}")

        with col2:
            st.subheader(f"{away_team}")
            st.write(f"FIFA Rank: {away_rank}")
            st.write(f"Last 5 Form: {away_form}")
            st.write(f"Goals Scored: {away_scored}")
            st.write(f"Goals Conceded: {away_conceded}")

        st.subheader("Head-to-Head History")
        h2h = get_head_to_head(home_team, away_team, date_obj)
        for match in h2h:
            st.write(match)



