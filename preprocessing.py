
import pandas as pd

def generate_features(home_team, away_team, tournament, match_country,
                      home_odds, draw_odds, away_odds, match_date, data):

    def calculate_form(team, date, data, n):
        matches = data[((data['home_team'] == team) | (data['away_team'] == team)) & (data['date'] < date)]
        matches = matches.sort_values(by='date', ascending=False).head(n)
        rating = 0
        for _, row in matches.iterrows():
            if (row["winner"] == "home_team" and row["home_team"] == team) or                (row["winner"] == "away_team" and row["away_team"] == team):
                rating += 3
            elif row["winner"] == "draw":
                rating += 1
        return rating

    def calculate_team_stats(team, date, data, n):
        matches = data[((data['home_team'] == team) | (data['away_team'] == team)) & (data['date'] < date)]
        matches = matches.sort_values(by='date', ascending=False).head(n)
        btts_count = 0
        goals_scored = 0
        goals_conceded = 0
        clean_sheets = 0
        for _, row in matches.iterrows():
            if row['home_team'] == team:
                scored = row['home_score']
                conceded = row['away_score']
            else:
                scored = row['away_score']
                conceded = row['home_score']
            goals_scored += scored
            goals_conceded += conceded
            if conceded == 0:
                clean_sheets += 1
            if row['btts'] == 1:
                btts_count += 1
        return btts_count, goals_scored, goals_conceded, goals_scored + goals_conceded, clean_sheets

    def get_latest_rank(team, date):
        ranks = data[(data['date'] <= date) & ((data['home_team'] == team) | (data['away_team'] == team))]
        ranks = ranks.sort_values(by='date', ascending=False)
        if not ranks.empty:
            if ranks.iloc[0]['home_team'] == team:
                return ranks.iloc[0]['home_rank']
            else:
                return ranks.iloc[0]['away_rank']
        else:
            return 100

    date = pd.to_datetime(match_date)

    home_form_5 = calculate_form(home_team, date, data, 5)
    away_form_5 = calculate_form(away_team, date, data, 5)
    home_form_10 = calculate_form(home_team, date, data, 10)
    away_form_10 = calculate_form(away_team, date, data, 10)

    home_advantage = 1 if home_team == match_country else 0

    stats = {}
    for n in [5, 10]:
        for side, team in zip(['home', 'away'], [home_team, away_team]):
            btts, scored, conceded, total, cs = calculate_team_stats(team, date, data, n)
            stats[f'Last_{n}btts_{side}'] = btts
            stats[f'Last_{n}total_scored_{side}'] = scored
            stats[f'Last_{n}total_conceded_{side}'] = conceded
            stats[f'Last_{n}total_{side}'] = total
            stats[f'Last_{n}cleansheets_{side}'] = cs

    for n in [5, 10]:
        stats[f'Last_{n}btts_total'] = stats[f'Last_{n}btts_home'] + stats[f'Last_{n}btts_away']
        stats[f'Last_{n}total_scored_total'] = stats[f'Last_{n}total_scored_home'] + stats[f'Last_{n}total_scored_away']
        stats[f'Last_{n}total_conceded_total'] = stats[f'Last_{n}total_conceded_home'] + stats[f'Last_{n}total_conceded_away']
        stats[f'Last_{n}total_total'] = stats[f'Last_{n}total_home'] + stats[f'Last_{n}total_away']
        stats[f'Last_{n}cleansheets_total'] = stats[f'Last_{n}cleansheets_home'] + stats[f'Last_{n}cleansheets_away']

    average_scored_5_home = stats['Last_5total_scored_home'] / 5
    average_scored_5_away = stats['Last_5total_scored_away'] / 5
    average_scored_10_home = stats['Last_10total_scored_home'] / 10
    average_scored_10_away = stats['Last_10total_scored_away'] / 10

    average_conceded_5_home = stats['Last_5total_conceded_home'] / 5
    average_conceded_5_away = stats['Last_5total_conceded_away'] / 5
    average_conceded_10_home = stats['Last_10total_conceded_home'] / 10
    average_conceded_10_away = stats['Last_10total_conceded_away'] / 10

    average_scored_5_diff = average_scored_5_home - average_scored_5_away
    average_scored_10_diff = average_scored_10_home - average_scored_10_away
    average_conceded_5_diff = average_conceded_5_home - average_conceded_5_away
    average_conceded_10_diff = average_conceded_10_home - average_conceded_10_away

    home_rank = get_latest_rank(home_team, date)
    away_rank = get_latest_rank(away_team, date)
    rank_diff = home_rank - away_rank

    prob_home = 1 / home_odds
    prob_draw = 1 / draw_odds
    prob_away = 1 / away_odds

    prob_2X = prob_draw + prob_away
    prob_1X = prob_draw + prob_home

    odds_margin = (1 / home_odds + 1 / draw_odds + 1 / away_odds) - 1
    odds_diff = max(prob_home, prob_draw, prob_away) - min(prob_home, prob_draw, prob_away)

    feature_dict = {
        'tournament_importance': 3 if tournament in ['FIFA World Cup', 'UEFA Euro'] else 2,
        'home_team_form_rating_5': home_form_5,
        'away_team_form_rating_5': away_form_5,
        'home_team_form_rating_10': home_form_10,
        'away_team_form_rating_10': away_form_10,
        'home_advantage': home_advantage,
        **stats,
        'average_scored_5_home': average_scored_5_home,
        'average_scored_5_away': average_scored_5_away,
        'average_scored_10_home': average_scored_10_home,
        'average_scored_10_away': average_scored_10_away,
        'average_scored_5_diff': average_scored_5_diff,
        'average_scored_10_diff': average_scored_10_diff,
        'average_conceded_5_home': average_conceded_5_home,
        'average_conceded_5_away': average_conceded_5_away,
        'average_conceded_10_home': average_conceded_10_home,
        'average_conceded_10_away': average_conceded_10_away,
        'average_conceded_5_diff': average_conceded_5_diff,
        'average_conceded_10_diff': average_conceded_10_diff,
        'home_rank': home_rank,
        'away_rank': away_rank,
        'rank_diff': rank_diff,
        'home_odds': home_odds,
        'draw_odds': draw_odds,
        'away_odds': away_odds,
        'prob_home': prob_home,
        'prob_draw': prob_draw,
        'prob_away': prob_away,
        'prob_2X': prob_2X,
        'prob_1X': prob_1X,
        'odds_margin': odds_margin,
        'odds_diff': odds_diff
    }

    return pd.DataFrame([feature_dict])
