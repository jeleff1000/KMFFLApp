import streamlit as st

class SeasonProjectedStatsViewer:
    def __init__(self, filtered_df, original_df):
        self.df = filtered_df.copy()
        self.original_df = original_df.copy()  # Always unfiltered

    def display(self, prefix=""):
        st.header("Season Projected Stats")
        required_columns = [
            'Manager', 'opponent', 'team_points', 'opponent_score', 'team_projected_points',
            'opponent_projected_points', 'Expected Odds', 'margin', 'Expected Spread', 'week', 'year',
            'Projected Score Error', 'Absolute Value Projected Score Error',
            'Projected Wins', 'Above Projected Score', 'Below Projected Score', 'Win Matchup Against the Spread',
            'Underdog Wins', 'Favorite Loses'
        ]
        if all(col in self.df.columns for col in required_columns):
            self.df['win'] = self.df['team_points'] > self.df['opponent_score']
            self.df['loss'] = self.df['team_points'] <= self.df['opponent_score']

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = self.df.groupby(['Manager', 'year']).agg({
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'team_projected_points': aggregation_func,
                'opponent_projected_points': aggregation_func,
                'Expected Odds': 'mean',
                'margin': aggregation_func,
                'Expected Spread': 'mean',
                'win': aggregation_func,
                'loss': aggregation_func,
                'Projected Wins': aggregation_func,
                'Above Projected Score': aggregation_func,
                'Below Projected Score': aggregation_func,
                'Win Matchup Against the Spread': aggregation_func,
                'Projected Score Error': aggregation_func,
                'Absolute Value Projected Score Error': aggregation_func,
                'Underdog Wins': aggregation_func,
                'Favorite Loses': aggregation_func
            }).reset_index()

            if aggregation_type:
                columns_to_round_2 = [
                    'team_points', 'opponent_score', 'team_projected_points', 'opponent_projected_points', 'margin',
                    'Expected Spread', 'Projected Score Error', 'Absolute Value Projected Score Error'
                ]
                columns_to_round_3 = [
                    'Expected Odds', 'Projected Wins', 'Above Projected Score', 'Below Projected Score', 'Win Matchup Against the Spread',
                    'Underdog Wins', 'Favorite Loses'
                ]
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            aggregated_df['year'] = aggregated_df['year'].astype(str)

            display_df = aggregated_df.rename(columns={
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA',
                'team_projected_points': 'Projected Pts',
                'opponent_projected_points': 'Opp Projected Pts',
                'Expected Odds': 'Expected Odds',
                'margin': 'Margin',
                'Expected Spread': 'Expected Margin',
                'Projected Wins': 'Projected W',
                'Above Projected Score': 'Above Projected Score',
                'Below Projected Score': 'Below Projected Score',
                'Win Matchup Against the Spread': 'W vs Spread',
                'Projected Score Error': 'Projected Score Error',
                'Absolute Value Projected Score Error': 'Absolute Value Proj Error',
                'Underdog Wins': 'Underdog Wins',
                'Favorite Loses': 'Favorite Loses'
            })

            display_df['accuracy rate'] = 1 - (
                (display_df['Underdog Wins'] + display_df['Favorite Loses']) / (display_df['W'] + display_df['L'])
            )
            display_df['accuracy rate'] = display_df['accuracy rate'].round(3)

            st.dataframe(display_df, hide_index=True)

            # --- Static Aggregated summary table (always unfiltered) ---
            original_df = self.original_df.copy()
            original_df['win'] = original_df['team_points'] > original_df['opponent_score']
            original_df['loss'] = original_df['team_points'] <= original_df['opponent_score']

            summary_df = original_df.groupby('year').agg({
                'win': 'sum',
                'loss': 'sum',
                'Projected Wins': 'sum',
                'Underdog Wins': 'sum',
                'Favorite Loses': 'sum',
                'team_points': 'sum',
                'team_projected_points': 'sum',
                'Above Projected Score': 'sum',
                'Below Projected Score': 'sum',
                'Projected Score Error': 'sum',
                'Absolute Value Projected Score Error': 'sum'
            }).reset_index()

            summary_df['year'] = summary_df['year'].astype(str)
            summary_df = summary_df.rename(columns={
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'Projected Wins': 'Projected W',
                'Underdog Wins': 'Underdog Wins',
                'Favorite Loses': 'Favorite Loses',
                'team_points': 'PF',
                'team_projected_points': 'Projected Points',
                'Above Projected Score': 'Above Projected Score',
                'Below Projected Score': 'Below Projected Score',
                'Projected Score Error': 'Projected Score Error',
                'Absolute Value Projected Score Error': 'Absolute Value Proj Error'
            })

            summary_df['accuracy rate'] = 1 - (
                    (summary_df['Underdog Wins'] + summary_df['Favorite Loses']) / (summary_df['W'] + summary_df['L'])
            )
            summary_df['accuracy rate'] = summary_df['accuracy rate'].round(3)
            summary_df = summary_df.drop(columns=['W', 'L', 'Projected W'])

            st.markdown("### Aggregated Season Summary (All Managers)")
            st.dataframe(summary_df, hide_index=True)