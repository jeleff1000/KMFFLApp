import pandas as pd
import streamlit as st

def display_weekly_optimal_lineup(matchup_df, player_df):
    # Merge player_df and matchup_df at the beginning
    merged_df = pd.merge(player_df, matchup_df, left_on=['owner', 'week', 'season'], right_on=['Manager', 'week', 'year'], how='left')

    # Remove rows where Manager is None
    merged_df = merged_df[merged_df['Manager'].notna()]

    # Keep only the specified columns
    columns_to_keep = ['Manager', 'week', 'year', 'team_points', 'win', 'loss', 'opponent', 'opponent_score', 'points', 'Included in optimal score', 'fantasy position', 'is_playoffs', 'is_consolation']
    filtered_df = merged_df[columns_to_keep]

    # Create a new column that sums the points when Included in optimal score is 1
    filtered_df['optimal_points_sum'] = filtered_df[filtered_df['Included in optimal score'] == 1].groupby(['Manager', 'week', 'year'])['points'].transform('sum')

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
    opponent_optimal_df = aggregated_df[['Manager', 'week', 'year', 'optimal_points_sum']].rename(columns={
        'Manager': 'opponent',
        'optimal_points_sum': 'opponent_optimal'
    })
    aggregated_df = pd.merge(
        aggregated_df,
        opponent_optimal_df,
        how='left',
        left_on=['opponent', 'week', 'year'],
        right_on=['opponent', 'week', 'year']
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
    aggregated_df = aggregated_df[['Manager', 'week', 'year', 'opponent', 'team_points', 'optimal_points', 'lost_points', 'win', 'loss', 'optimal_win', 'optimal_loss', 'opponent_score', 'opponent_optimal']]

    # Rename columns
    aggregated_df = aggregated_df.rename(columns={
        'week': 'Week',
        'year': 'Year',
        'opponent': 'Opponent',
        'team_points': 'Team Points',
        'optimal_points': 'Optimal Points',
        'lost_points': 'Lost Points',
        'win': 'Win',
        'loss': 'Loss',
        'optimal_win': 'Optimal Win',
        'optimal_loss': 'Optimal Loss',
        'opponent_score': 'Opp Pts',
        'opponent_optimal': 'Opp Optimal'
    })

    # Display the aggregated DataFrame
    st.dataframe(aggregated_df, hide_index=True)

if __name__ == "__main__":
    # Example usage
    player_data = pd.DataFrame()  # Replace with actual player data
    matchup_data = pd.DataFrame()  # Replace with actual matchup data
    display_weekly_optimal_lineup(matchup_data, player_data)