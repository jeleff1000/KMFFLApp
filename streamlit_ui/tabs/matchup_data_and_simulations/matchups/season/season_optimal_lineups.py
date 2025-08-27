import pandas as pd
import streamlit as st

def get_optimal_summary(player_df, matchup_data):
    merged_df = pd.merge(
        player_df, matchup_data,
        left_on=['owner', 'week', 'season', 'opponent'],
        right_on=['Manager', 'week', 'year', 'opponent'],
        how='left'
    )
    merged_df = merged_df[merged_df['Manager'].notna()]
    columns_to_keep = [
        'Manager', 'week', 'year', 'team_points', 'win', 'loss', 'opponent',
        'opponent_score', 'points', 'optimal_player', 'fantasy position', 'is_playoffs', 'is_consolation'
    ]
    filtered_df = merged_df[columns_to_keep]
    filtered_df['optimal_points_sum'] = filtered_df[filtered_df['optimal_player'] == 1].groupby(['Manager', 'week', 'year'])['points'].transform('sum')
    aggregated_df = filtered_df.groupby(['Manager', 'week', 'year', 'opponent']).agg({
        'team_points': 'first',
        'win': 'first',
        'loss': 'first',
        'opponent_score': 'first',
        'points': 'sum',
        'optimal_points_sum': 'first',
        'is_playoffs': 'first',
        'is_consolation': 'first'
    }).reset_index()
    aggregated_df = pd.merge(
        aggregated_df,
        aggregated_df[['Manager', 'week', 'year', 'optimal_points_sum']].rename(columns={
            'Manager': 'opponent',
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
    season_aggregated_df = aggregated_df.groupby(['Manager', 'year']).agg({
        'win': 'sum',
        'loss': 'sum',
        'optimal_win': 'sum',
        'optimal_loss': 'sum',
        'team_points': 'sum',
        'optimal_points': 'sum',
        'lost_points': 'sum',
        'opponent_score': 'sum',
        'opponent_optimal': 'sum'
    }).reset_index()
    summary_df = season_aggregated_df.groupby('year').agg({
        'team_points': 'sum',
        'optimal_points': 'sum',
        'lost_points': 'sum'
    }).reset_index()
    num_games = aggregated_df.groupby('year').size().reset_index(name='num_games')
    summary_df = pd.merge(summary_df, num_games, on='year')
    for col in ['team_points', 'optimal_points', 'lost_points']:
        summary_df[col] = (summary_df[col] / summary_df['num_games']).round(2)
    summary_df.drop(columns=['num_games'], inplace=True)
    summary_df = summary_df.rename(columns={
        'year': 'Year',
        'team_points': 'PF',
        'optimal_points': 'Optimal PF',
        'lost_points': 'Lost Points'
    })
    return summary_df

def display_season_optimal_lineup(player_df, filtered_matchup_data, unfiltered_matchup_data):
    if 'Manager' not in filtered_matchup_data.columns:
        st.error("The filtered_matchup_data DataFrame does not contain the 'Manager' column.")
        return

    # --- Main table calculation (filtered) ---
    merged_df = pd.merge(
        player_df, filtered_matchup_data,
        left_on=['owner', 'week', 'season', 'opponent'],
        right_on=['Manager', 'week', 'year', 'opponent'],
        how='left'
    )
    merged_df = merged_df[merged_df['Manager'].notna()]
    columns_to_keep = [
        'Manager', 'week', 'year', 'team_points', 'win', 'loss', 'opponent',
        'opponent_score', 'points', 'optimal_player', 'fantasy position', 'is_playoffs', 'is_consolation'
    ]
    filtered_df = merged_df[columns_to_keep]
    filtered_df['optimal_points_sum'] = filtered_df[filtered_df['optimal_player'] == 1].groupby(['Manager', 'week', 'year'])['points'].transform('sum')
    aggregated_df = filtered_df.groupby(['Manager', 'week', 'year', 'opponent']).agg({
        'team_points': 'first',
        'win': 'first',
        'loss': 'first',
        'opponent_score': 'first',
        'points': 'sum',
        'optimal_points_sum': 'first',
        'is_playoffs': 'first',
        'is_consolation': 'first'
    }).reset_index()
    aggregated_df = pd.merge(
        aggregated_df,
        aggregated_df[['Manager', 'week', 'year', 'optimal_points_sum']].rename(columns={
            'Manager': 'opponent',
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
    aggregated_df = aggregated_df[['Manager', 'week', 'year', 'opponent', 'win', 'loss', 'optimal_win', 'optimal_loss',
                                   'opponent_score', 'opponent_optimal', 'team_points', 'optimal_points', 'lost_points',
                                   'is_playoffs', 'is_consolation']]
    season_aggregated_df = aggregated_df.groupby(['Manager', 'year']).agg({
        'win': 'sum',
        'loss': 'sum',
        'optimal_win': 'sum',
        'optimal_loss': 'sum',
        'team_points': 'sum',
        'optimal_points': 'sum',
        'lost_points': 'sum',
        'opponent_score': 'sum',
        'opponent_optimal': 'sum'
    }).reset_index()
    per_game = st.toggle("Per Game", value=False, key="per_game_toggle")
    if per_game:
        num_games = aggregated_df.groupby(['Manager', 'year']).size().reset_index(name='num_games')
        season_aggregated_df = pd.merge(season_aggregated_df, num_games, on=['Manager', 'year'])
        for col in ['team_points', 'win', 'loss', 'optimal_points', 'lost_points', 'optimal_win', 'optimal_loss', 'opponent_score', 'opponent_optimal']:
            season_aggregated_df[col] = (season_aggregated_df[col] / season_aggregated_df['num_games']).round(2)
        season_aggregated_df.drop(columns=['num_games'], inplace=True)
    season_aggregated_df = season_aggregated_df.rename(columns={
        'Manager': 'Manager',
        'year': 'Year',
        'win': 'W',
        'loss': 'L',
        'optimal_win': 'Optimal W',
        'optimal_loss': 'Optimal L',
        'team_points': 'PF',
        'optimal_points': 'Optimal PF',
        'lost_points': 'Lost Points',
        'opponent_score': 'PA',
        'opponent_optimal': 'Opp Optimal'
    })
    st.markdown("### Season Optimal Stats (By Manager)")
    st.dataframe(season_aggregated_df, hide_index=True)

    # --- Static summary table (always unfiltered) ---
    summary_df = get_optimal_summary(player_df, unfiltered_matchup_data)
    st.markdown("### Season Optimal Stats (Aggregated)")
    st.dataframe(summary_df, hide_index=True)
