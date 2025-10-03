import pandas as pd
import streamlit as st

def get_optimal_summary(player_df, matchup_data):
    # This function is no longer used in the display function below
    pass

def display_season_optimal_lineup(player_df, filtered_matchup_data, unfiltered_matchup_data):
    if 'manager' not in filtered_matchup_data.columns:
        st.error("The filtered_matchup_data DataFrame does not contain the 'manager' column.")
        return

    # --- Main table calculation (filtered) ---
    merged_df = pd.merge(
        player_df, filtered_matchup_data,
        left_on=['manager', 'week', 'year', 'opponent'],
        right_on=['manager', 'week', 'year', 'opponent'],
        how='left'
    )
    merged_df = merged_df[merged_df['manager'].notna()]
    columns_to_keep = [
        'manager', 'week', 'year', 'team_points', 'win', 'loss', 'opponent',
        'opponent_points', 'points', 'optimal_player', 'fantasy_position', 'is_playoffs', 'is_consolation'
    ]
    filtered_df = merged_df[columns_to_keep]
    filtered_df['optimal_points_sum'] = filtered_df[filtered_df['optimal_player'] == 1].groupby(['manager', 'week', 'year'])['points'].transform('sum')
    aggregated_df = filtered_df.groupby(['manager', 'week', 'year', 'opponent']).agg({
        'team_points': 'first',
        'win': 'first',
        'loss': 'first',
        'opponent_points': 'first',
        'points': 'sum',
        'optimal_points_sum': 'first',
        'is_playoffs': 'first',
        'is_consolation': 'first'
    }).reset_index()
    aggregated_df = pd.merge(
        aggregated_df,
        aggregated_df[['manager', 'week', 'year', 'optimal_points_sum']].rename(columns={
            'manager': 'opponent',
            'optimal_points_sum': 'opponent_optimal'
        }),
        how='left',
        on=['opponent', 'week', 'year']
    )
    aggregated_df.rename(columns={'optimal_points_sum': 'optimal_points'}, inplace=True)
    aggregated_df['optimal_win'] = (aggregated_df['optimal_points'] > aggregated_df['opponent_optimal']).astype(bool)
    aggregated_df['optimal_loss'] = (aggregated_df['optimal_points'] <= aggregated_df['opponent_optimal']).astype(bool)
    aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)
    aggregated_df['win'] = aggregated_df['win'].astype(bool)
    aggregated_df['loss'] = aggregated_df['loss'].astype(bool)
    aggregated_df['lost_points'] = aggregated_df['optimal_points'] - aggregated_df['team_points']
    aggregated_df = aggregated_df[['manager', 'week', 'year', 'opponent', 'win', 'loss', 'optimal_win', 'optimal_loss',
                                   'opponent_points', 'opponent_optimal', 'team_points', 'optimal_points', 'lost_points',
                                   'is_playoffs', 'is_consolation']]
    year_aggregated_df = aggregated_df.groupby(['manager', 'year']).agg({
        'win': 'sum',
        'loss': 'sum',
        'optimal_win': 'sum',
        'optimal_loss': 'sum',
        'team_points': 'sum',
        'optimal_points': 'sum',
        'lost_points': 'sum',
        'opponent_points': 'sum',
        'opponent_optimal': 'sum'
    }).reset_index()
    per_game = st.toggle("Per Game", value=False, key="per_game_toggle")
    if per_game:
        num_games = aggregated_df.groupby(['manager', 'year']).size().reset_index(name='num_games')
        year_aggregated_df = pd.merge(year_aggregated_df, num_games, on=['manager', 'year'])
        for col in ['team_points', 'win', 'loss', 'optimal_points', 'lost_points', 'optimal_win', 'optimal_loss', 'opponent_points', 'opponent_optimal']:
            year_aggregated_df[col] = (year_aggregated_df[col] / year_aggregated_df['num_games']).round(2)
        year_aggregated_df.drop(columns=['num_games'], inplace=True)
    year_aggregated_df = year_aggregated_df.rename(columns={
        'manager': 'manager',
        'year': 'Year',
        'win': 'W',
        'loss': 'L',
        'optimal_win': 'Optimal W',
        'optimal_loss': 'Optimal L',
        'team_points': 'PF',
        'optimal_points': 'Optimal PF',
        'lost_points': 'Lost Points',
        'opponent_points': 'PA',
        'opponent_optimal': 'Opp Optimal'
    })
    st.markdown("### Season Optimal Stats")
    st.dataframe(year_aggregated_df, hide_index=True)