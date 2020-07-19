from typing import List, Tuple

import requests
import pandas as pd
import lxml
import html5lib
import bs4
import json


# Automated Program to download geoguessr results table, to play blackjack with
def geoguessr_blackjack(message, players):
    url, lower_score, higher_score = message.split(' ')
    lower_score, higher_score = int(lower_score), int(higher_score)
    url = 'https://geoguessr.com/api/v3/results/scores{}/0/10000'.format(url.split('results')[1])
    all_scores = retrieve_all_scores(url)
    players = filter_player_scores(all_scores, players, lower_score, higher_score)
    return players


# retrieves all scores using requests, and pandas read_html method
def retrieve_all_scores(url) -> pd.DataFrame:
    html = requests.get(url).content
    df = pd.DataFrame(
        json.loads(html)
    ).drop(columns=['gameToken', 'userId', 'isActive', 'isLeader', 'pinUrl', 'color'])
    return df


# filters player scores based on player already existing in game, and if their score was correct
def filter_player_scores(all_scores: pd.DataFrame, players: List, lower_score: int, higher_score: int) -> Tuple[List[str], List[str]]:
    if len(players) > 0:
        player_filter = all_scores['playerName'].isin(players)
        all_scores = all_scores[player_filter]

    # deals with final round logic to find closest player to score
    if lower_score == higher_score:
        all_scores.loc[:, 'diff'] = all_scores.apply(
            lambda row: abs(row['totalScore'] - lower_score),
            axis=1
        )
        all_scores = all_scores.sort_values(by='diff')
        min_diff = all_scores.iloc[0]['diff']
        filter_higher = all_scores['totalScore'] == (lower_score + min_diff)
        filter_lower = all_scores['totalScore'] == (lower_score - min_diff)
        all_scores = all_scores[filter_higher | filter_lower]
        return list(all_scores['playerName']), list(all_scores['totalScore'])

    lower_filter = all_scores['totalScore'] >= lower_score
    higher_filter = all_scores['totalScore'] <= higher_score
    all_scores = all_scores[lower_filter & higher_filter]
    return list(all_scores['playerName']), list(all_scores['totalScore'])
