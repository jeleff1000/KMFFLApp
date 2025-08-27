import pandas as pd
import streamlit as st

def display_season_optimal_lineup(player_df, matchup_data):
    # Ensure the matchup_data DataFrame has the 'Manager' column
    if 'Manager' not in matchup_data.columns:
        st.error("The matchup_data DataFrame does not contain the 'Manager' column.")
        return

    # Merge player_df and matchup_data at the beginning
    merged_df = pd.merge(player_df, matchup_data, left_on=['owner', 'week', 'season', 'opponent'], right_on=['Manager', 'week', 'year', 'opponent'], how='left')

    # Remove rows where Manager is None
    merged_df = merged_df[merged_df['Manager'].notna()]

    # Keep only the specified columns
    columns_to_keep = ['Manager', 'week', 'year', 'team_points', 'win', 'loss', 'opponent', 'opponent_score', 'points', 'optimal_player', 'fantasy position', 'is_playoffs', 'is_consolation']
    filtered_df = merged_df[columns_to_keep]

    # Create a new column that sums the points when optimal_player is 1
    filtered_df['optimal_points_sum'] = filtered_df[filtered_df['optimal_player'] == 1].groupby(['Manager', 'week', 'year'])['points'].transform('sum')

    # Aggregate the data on Manager, week, and year
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

    # Self-join to get opponent's optimal_points_sum
    aggregated_df = pd.merge(
        aggregated_df,
        aggregated_df[['Manager', 'week', 'year', 'optimal_points_sum']].rename(columns={
            'Manager': 'opponent',
            'optimal_points_sum': 'opponent_optimal'
        }),
        how='left',
        on=['opponent', 'week', 'year']
    )

    # Rename optimal_points_sum to optimal_points
    aggregated_df.rename(columns={'optimal_points_sum': 'optimal_points'}, inplace=True)

    # Create optimal_win and optimal_loss columns
    aggregated_df['optimal_win'] = (aggregated_df['optimal_points'] > aggregated_df['opponent_optimal']).astype(bool)
    aggregated_df['optimal_loss'] = (aggregated_df['optimal_points'] <= aggregated_df['opponent_optimal']).astype(bool)

    # Convert year to integer to remove decimal and then to string to remove commas
    aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)

    # Convert win and loss to boolean
    aggregated_df['win'] = aggregated_df['win'].astype(bool)
    aggregated_df['loss'] = aggregated_df['loss'].astype(bool)

    # Calculate lost_points as team_points - optimal_points
    aggregated_df['lost_points'] = aggregated_df['optimal_points'] - aggregated_df['team_points']

    # Reorder columns
    aggregated_df = aggregated_df[['Manager', 'week', 'year', 'opponent','win', 'loss', 'optimal_win', 'optimal_loss', 'opponent_score', 'opponent_optimal',  'team_points', 'optimal_points', 'lost_points', 'is_playoffs', 'is_consolation']]

    # Aggregate the data on Manager and year
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

    # Add toggle for per game calculation
    per_game = st.toggle("Per Game", value=False, key="per_game_toggle")

    if per_game:
        # Calculate the number of games in scope
        num_games = aggregated_df.groupby(['Manager', 'year']).size().reset_index(name='num_games')
        season_aggregated_df = pd.merge(season_aggregated_df, num_games, on=['Manager', 'year'])

        # Divide relevant columns by the number of games and round to 2 decimals
        for col in ['team_points', 'win', 'loss', 'optimal_points', 'lost_points', 'optimal_win', 'optimal_loss', 'opponent_score', 'opponent_optimal']:
            season_aggregated_df[col] = (season_aggregated_df[col] / season_aggregated_df['num_games']).round(2)

        # Drop the num_games column
        season_aggregated_df.drop(columns=['num_games'], inplace=True)

    # Rename columns
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

    # Display the main table
    st.markdown("### Season Optimal Stats (By Manager)")
    st.dataframe(season_aggregated_df, hide_index=True)

    # Aggregate across all managers for each year
    summary_df = season_aggregated_df.groupby('Year').agg({
        'PF': 'sum',
        'Optimal PF': 'sum',
        'Lost Points': 'sum'
    }).reset_index()

    # Calculate total number of games per year
    num_games = aggregated_df.groupby('year').size().reset_index(name='num_games')
    num_games.rename(columns={'year': 'Year'}, inplace=True)

    # Merge and calculate per game stats
    summary_df = pd.merge(summary_df, num_games, on='Year')
    for col in ['PF', 'Optimal PF', 'Lost Points']:
        summary_df[col] = (summary_df[col] / summary_df['num_games']).round(2)
    summary_df.drop(columns=['num_games'], inplace=True)

    st.markdown("### Season Optimal Stats (All Managers, Per Game)")
    st.dataframe(summary_df, hide_index=True)