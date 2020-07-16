from typing import List

import requests
import pandas as pd
import lxml


# Automated Program to download geoguessr results table, to play blackjack with
def geoguessr_blackjack(message, players):
    url, lower_score, higher_score = message.split(' ')
    lower_score, higher_score = int(lower_score), int(higher_score)
    all_scores = retrieve_all_scores(url)
    all_scores = format_scores_df(all_scores)
    players = filter_player_scores(all_scores, players, lower_score, higher_score)
    return players


# retrieves all scores using requests, and pandas read_html method
def retrieve_all_scores(url) -> pd.DataFrame:
    html = requests.get(url).content
    df_list = pd.read_html(html)
    df = df_list[-1]
    return df


# formats scores into easier format to work with
def format_scores_df(all_scores: pd.DataFrame) -> pd.DataFrame:
    all_scores = all_scores.drop(axis=1, labels=0).rename(columns={1: 'player', 2: 'score'})
    all_scores['score'] = all_scores['score'].apply(
        lambda row: int(row.split(' points')[0].replace(',', ''))
    )
    return all_scores


# filters player scores based on player already existing in game, and if their score was correct
def filter_player_scores(all_scores: pd.DataFrame, players: List, lower_score: int, higher_score: int) -> List[str]:
    if len(players) > 0:
        player_filter = all_scores['player'].isin(players)
        all_scores = all_scores[player_filter]

    # deals with final round logic to find closest player to score
    if lower_score == higher_score:
        all_scores.loc[:, 'diff'] = all_scores.apply(
            lambda row: abs(row['score'] - lower_score),
            axis=1
        )
        all_scores = all_scores.sort_values(by='diff')
        return [all_scores.iloc[0]['player']]

    lower_filter = all_scores['score'] >= lower_score
    higher_filter = all_scores['score'] <= higher_score
    all_scores = all_scores[lower_filter & higher_filter]
    return list(all_scores['player'])
