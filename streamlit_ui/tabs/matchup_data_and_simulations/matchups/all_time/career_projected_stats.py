import streamlit as st

class SeasonProjectedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Career Projected Stats")
        required_columns = [
            'manager', 'opponent', 'team_points', 'opponent_score', 'team_projected_points',
            'opponent_projected_points', 'expected_odds', 'margin', 'expected_spread', 'manager_week', 'manager_year',
            'proj_score_error', 'abs_proj_score_error'
        ]
        if all(col in self.df.columns for col in required_columns):
            self.df['win'] = self.df['team_points'] > self.df['opponent_score']
            self.df['loss'] = self.df['team_points'] <= self.df['opponent_score']
            self.df['projected_wins'] = self.df['team_projected_points'] > self.df['opponent_projected_points']
            self.df['above_proj_score'] = self.df['team_points'] > self.df['team_projected_points']
            self.df['win_vs_spread'] = (self.df['team_points'] - self.df['opponent_score']) > self.df['expected_spread']

            aggregation_type = st.toggle("Average", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = self.df.groupby('manager').agg({
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'team_projected_points': aggregation_func,
                'opponent_projected_points': aggregation_func,
                'expected_odds': 'mean',
                'margin': aggregation_func,
                'expected_spread': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'projected_wins': aggregation_func,
                'above_proj_score': aggregation_func,
                'win_vs_spread': aggregation_func,
                'proj_score_error': aggregation_func,
                'abs_proj_score_error': aggregation_func
            }).reset_index()

            if aggregation_type:
                columns_to_round_2 = [
                    'team_points', 'opponent_score', 'team_projected_points', 'opponent_projected_points', 'margin',
                    'expected_spread', 'proj_score_error', 'abs_proj_score_error'
                ]
                columns_to_round_3 = [
                    'expected_odds', 'projected_wins', 'above_proj_score', 'win_vs_spread'
                ]
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            # Rename columns for display
            aggregated_df = aggregated_df.rename(columns={
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA',
                'team_projected_points': 'Projected PF',
                'opponent_projected_points': 'Projected Average',
                'expected_odds': 'Expected Odds',
                'margin': 'Margin',
                'expected_spread': 'Expected Margin',
                'projected_wins': 'Projected W',
                'above_proj_score': 'Above Projected Score',
                'win_vs_spread': 'W vs Spread',
                'proj_score_error': 'Projected Score Error',
                'abs_proj_score_error': 'Absolute Value Projected Score Error'
            })

            # Set the index to manager
            aggregated_df.set_index('manager', inplace=True)

            display_df = aggregated_df[['W', 'L', 'PF', 'PA', 'Projected PF', 'Projected Average', 'Expected Odds', 'Margin', 'Expected Margin', 'Projected W', 'Above Projected Score', 'W vs Spread', 'Projected Score Error', 'Absolute Value Projected Score Error']]
            st.dataframe(display_df)
        else:
            st.write("The required columns are not available in the data.")