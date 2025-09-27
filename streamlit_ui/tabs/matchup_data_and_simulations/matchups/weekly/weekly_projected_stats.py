import streamlit as st
import pandas as pd
class WeeklyProjectedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Weekly Projected Stats")
        required_columns = [
            'manager', 'opponent', 'team_points', 'opponent_score', 'team_projected_points',
            'opponent_projected_points', 'expected_odds', 'margin', 'expected_spread', 'week', 'year',
            'proj_score_error', 'abs_proj_score_error'
        ]
        if all(col in self.df.columns for col in required_columns):
            self.df['win'] = self.df['team_points'] > self.df['opponent_score']
            self.df['projected_wins'] = self.df['team_projected_points'] > self.df['opponent_projected_points']
            self.df['above_proj_score'] = self.df['team_points'] > self.df['team_projected_points']
            self.df['win_vs_spread'] = (self.df['team_points'] - self.df['opponent_score']) > self.df['expected_spread']

            display_df = self.df[[
                'manager', 'week', 'year', 'opponent', 'team_points', 'opponent_score', 'team_projected_points',
                'opponent_projected_points', 'expected_odds', 'margin', 'expected_spread',
                'win', 'projected_wins', 'above_proj_score', 'win_vs_spread',
                'proj_score_error', 'abs_proj_score_error'
            ]]
            display_df = display_df.rename(columns={
                'manager': 'Manager',
                'week': 'Week',
                'year': 'Year',
                'opponent': 'Opponent',
                'team_points': 'Team Points',
                'opponent_score': 'Opp Pts',
                'team_projected_points': 'Proj. Pts',
                'opponent_projected_points': 'Opp Proj. Pts',
                'expected_odds': 'Expected Odds',
                'margin': 'Margin',
                'expected_spread': 'Expected Spread',
                'win': 'Win',
                'projected_wins': 'Projected Win',
                'above_proj_score': 'Above Projected Score',
                'win_vs_spread': 'Win Matchup Against the Spread',
                'proj_score_error': 'Projected Score Error',
                'abs_proj_score_error': 'Absolute Value Projected Score Error'
            })
            # Safely convert Year to int string if possible, else keep as string
            display_df['Year'] = display_df['Year'].apply(
                lambda x: f"{int(float(x))}" if pd.notnull(x) and str(x).replace('.', '', 1).isdigit() else str(x)
            )
            display_df = display_df.sort_values(by=['Year', 'Week']).reset_index(drop=True)
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Manager": {"frozen": True},
                    "Week": {"frozen": True},
                    "Year": {"frozen": True}
                }
            )
        else:
            st.write("The required columns are not available in the data.")
