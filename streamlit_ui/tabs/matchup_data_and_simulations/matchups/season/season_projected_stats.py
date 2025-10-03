import streamlit as st

class SeasonProjectedStatsViewer:
    def __init__(self, filtered_df, original_df):
        self.df = filtered_df.copy()
        self.original_df = original_df.copy()  # Always unfiltered

    def display(self, prefix=""):
        st.header("Season Projected Stats")
        required_columns = [
            'manager', 'opponent', 'team_points', 'opponent_points', 'team_projected_points',
            'opponent_projected_points', 'expected_odds', 'margin', 'expected_spread', 'manager_week', 'year',
            'proj_score_error', 'abs_proj_score_error',
            'proj_wins', 'above_proj_score', 'below_proj_score', 'win_vs_spread',
            'underdog_wins', 'favorite_losses'
        ]
        if all(col in self.df.columns for col in required_columns):
            self.df['win'] = self.df['team_points'] > self.df['opponent_points']
            self.df['loss'] = self.df['team_points'] <= self.df['opponent_points']

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = self.df.groupby(['manager', 'year']).agg({
                'team_points': aggregation_func,
                'opponent_points': aggregation_func,
                'team_projected_points': aggregation_func,
                'opponent_projected_points': aggregation_func,
                'expected_odds': 'mean',
                'margin': aggregation_func,
                'expected_spread': 'mean',
                'win': aggregation_func,
                'loss': aggregation_func,
                'proj_wins': aggregation_func,
                'above_proj_score': aggregation_func,
                'below_proj_score': aggregation_func,
                'win_vs_spread': aggregation_func,
                'proj_score_error': aggregation_func,
                'abs_proj_score_error': aggregation_func,
                'underdog_wins': aggregation_func,
                'favorite_losses': aggregation_func
            }).reset_index()

            if aggregation_type:
                columns_to_round_2 = [
                    'team_points', 'opponent_points', 'team_projected_points', 'opponent_projected_points', 'margin',
                    'expected_spread', 'proj_score_error', 'abs_proj_score_error'
                ]
                columns_to_round_3 = [
                    'expected_odds', 'proj_wins', 'above_proj_score', 'below_proj_score', 'win_vs_spread',
                    'underdog_wins', 'favorite_losses'
                ]
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            aggregated_df['year'] = aggregated_df['year'].astype(str)

            display_df = aggregated_df.rename(columns={
                'manager': 'Manager',
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_points': 'PA',
                'team_projected_points': 'Projected Pts',
                'opponent_projected_points': 'Opp Projected Pts',
                'expected_odds': 'Expected Odds',
                'margin': 'Margin',
                'expected_spread': 'Expected Margin',
                'proj_wins': 'Projected W',
                'above_proj_score': 'Above Projected Score',
                'below_proj_score': 'Below Projected Score',
                'win_vs_spread': 'W vs Spread',
                'proj_score_error': 'Projected Score Error',
                'abs_proj_score_error': 'Absolute Value Proj Error',
                'underdog_wins': 'Underdog Wins',
                'favorite_losses': 'Favorite Loses'
            })

            display_df['accuracy rate'] = 1 - (
                (display_df['Underdog Wins'] + display_df['Favorite Loses']) / (display_df['W'] + display_df['L'])
            )
            display_df['accuracy rate'] = display_df['accuracy rate'].round(3)

            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required columns are not available in the data.")