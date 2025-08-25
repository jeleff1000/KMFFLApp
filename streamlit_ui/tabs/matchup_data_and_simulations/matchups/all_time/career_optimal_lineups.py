import pandas as pd
import streamlit as st

def display_career_optimal_lineup(player_df, matchup_data, prefix=""):
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
    aggregated_df = aggregated_df[['Manager', 'week', 'year', 'opponent', 'win', 'loss', 'optimal_win', 'optimal_loss', 'team_points', 'optimal_points', 'lost_points', 'opponent_score', 'opponent_optimal', 'is_playoffs', 'is_consolation']]

    # Aggregate the data on Manager
    career_aggregated_df = aggregated_df.groupby(['Manager']).agg({
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
    per_game = st.toggle("Per Game", value=False, key=f"{prefix}_per_game_toggle")

    if per_game:
        # Calculate the number of games in scope
        num_games = aggregated_df.groupby(['Manager']).size().reset_index(name='num_games')
        career_aggregated_df = pd.merge(career_aggregated_df, num_games, on='Manager')

        # Divide relevant columns by the number of games and round to 2 decimals
        for col in ['win', 'loss', 'optimal_win', 'optimal_loss', 'team_points', 'optimal_points', 'lost_points', 'opponent_score', 'opponent_optimal']:
            career_aggregated_df[col] = (career_aggregated_df[col] / career_aggregated_df['num_games']).round(2)

        # Drop the num_games column
        career_aggregated_df.drop(columns=['num_games'], inplace=True)

    # Rename columns
    career_aggregated_df = career_aggregated_df.rename(columns={
        'Manager': 'Manager',
        'win': 'W',
        'loss': 'L',
        'optimal_win': 'Optimal W',
        'optimal_loss': 'Optimal L',
        'team_points': 'PF',
        'optimal_points': 'Optimal PF',
        'lost_points': 'Lost Points',
        'opponent_score': 'PA',
        'opponent_optimal': 'Optimal PA'
    })

    # Display the career aggregated DataFrame
    st.dataframe(career_aggregated_df, hide_index=True)

if __name__ == "__main__":
    # Example usage
    player_data = pd.DataFrame()  # Replace with actual player data
    matchup_data = pd.DataFrame()  # Replace with actual matchup data
    display_career_optimal_lineup(player_data, matchup_data, prefix="career")