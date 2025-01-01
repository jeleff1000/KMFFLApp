import pandas as pd
import numpy as np

def calculate_std_dev(df, selected_year, show_regular_season, show_postseason):
    # Filter data based on selections
    if selected_year != "All Years":
        df = df[df['year'] == selected_year]

    if not show_regular_season:
        df = df[df['is_playoffs'] == True]
    if not show_postseason:
        df = df[df['is_playoffs'] == False]

    # Group by Manager and calculate standard deviation of team_points
    std_dev_df = df.groupby('Manager')['team_points'].std().reset_index()
    std_dev_df.columns = ['Manager', 'StdDev_TeamPoints']

    return std_dev_df

def tweak_scores(df, std_dev_df):
    # Merge the standard deviation data with the original DataFrame
    df = df.merge(std_dev_df, on='Manager', how='left')

    # Tweak the scores by adding or subtracting up to 1/3 of the Manager's std_dev
    df['tweaked_team_points'] = df.apply(
        lambda row: row['team_points'] + np.random.uniform(-1/3, 1/3) * row['StdDev_TeamPoints'], axis=1
    )

    # Initialize Sim_Wins and Sim_Losses columns
    df['Sim_Wins'] = 0
    df['Sim_Losses'] = 0

    # Update Sim_Wins and Sim_Losses based on tweaked scores
    for index, row in df.iterrows():
        opponent_week = df[(df['Manager'] == row['opponent']) & (df['week'] == row['week'])]
        if not opponent_week.empty:
            opponent_points = opponent_week.iloc[0]['team_points']
            if row['tweaked_team_points'] > opponent_points:
                df.at[index, 'Sim_Wins'] = 1
            elif row['tweaked_team_points'] < opponent_points:
                df.at[index, 'Sim_Losses'] = 1

    return df

def calculate_playoff_seed(df):
    # Aggregate wins and tweaked_team_points for each manager
    agg_df = df.groupby('Manager').agg(
        Sim_Wins=('Sim_Wins', 'sum'),
        Total_Tweaked_Points=('tweaked_team_points', 'sum')
    ).reset_index()

    # Sort by Sim_Wins (descending) and Total_Tweaked_Points (descending)
    agg_df = agg_df.sort_values(by=['Sim_Wins', 'Total_Tweaked_Points'], ascending=[False, False])

    # Assign playoff seeds
    agg_df['Sim_Playoff_Seed'] = range(1, len(agg_df) + 1)

    # Merge the playoff seeds back to the original DataFrame
    df = df.merge(agg_df[['Manager', 'Sim_Playoff_Seed']], on='Manager', how='left')

    return df

# Example usage
def main(df, selected_year, show_regular_season, show_postseason, tweak_scores_flag):
    std_dev_df = calculate_std_dev(df, selected_year, show_regular_season, show_postseason)
    if tweak_scores_flag:
        df = tweak_scores(df, std_dev_df)
    df = calculate_playoff_seed(df)
    return df