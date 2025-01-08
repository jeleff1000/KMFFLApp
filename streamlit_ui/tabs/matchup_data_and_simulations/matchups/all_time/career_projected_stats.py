import streamlit as st

class SeasonProjectedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Career Projected Stats")
        required_columns = ['Manager', 'opponent', 'team_points', 'opponent_score', 'team_projected_points',
                            'opponent_projected_points', 'Expected Odds', 'margin', 'Expected Spread', 'week', 'year',
                            'Projected Score Error', 'Absolute Value Projected Score Error']
        if all(col in self.df.columns for col in required_columns):
            self.df['win'] = self.df['team_points'] > self.df['opponent_score']
            self.df['loss'] = self.df['team_points'] <= self.df['opponent_score']
            self.df['Projected Wins'] = self.df['team_projected_points'] > self.df['opponent_projected_points']
            self.df['Above Projected Score'] = self.df['team_points'] > self.df['team_projected_points']
            self.df['Win Matchup Against the Spread'] = (self.df['team_points'] - self.df['opponent_score']) > self.df['Expected Spread']

            aggregation_type = st.toggle("Average", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = self.df.groupby('Manager').agg({
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'team_projected_points': aggregation_func,
                'opponent_projected_points': aggregation_func,
                'Expected Odds': 'mean',
                'margin': aggregation_func,
                'Expected Spread': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'Projected Wins': aggregation_func,
                'Above Projected Score': aggregation_func,
                'Win Matchup Against the Spread': aggregation_func,
                'Projected Score Error': aggregation_func,
                'Absolute Value Projected Score Error': aggregation_func
            }).reset_index()

            if aggregation_type:
                columns_to_round_2 = [
                    'team_points', 'opponent_score', 'team_projected_points', 'opponent_projected_points', 'margin',
                    'Expected Spread', 'Projected Score Error', 'Absolute Value Projected Score Error'
                ]
                columns_to_round_3 = [
                    'Expected Odds', 'Projected Wins', 'Above Projected Score', 'Win Matchup Against the Spread'
                ]
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            # Rename columns
            aggregated_df = aggregated_df.rename(columns={
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA',
                'team_projected_points': 'Projected PF',
                'opponent_projected_points': 'Projected Average',
                'Expected Odds': 'Expected Odds',
                'margin': 'Margin',
                'Expected Spread': 'Expected Margin',
                'Projected Wins': 'Projected W',
                'Above Projected Score': 'Above Projected Score',
                'Win Matchup Against the Spread': 'W vs Spread',
                'Projected Score Error': 'Projected Score Error',
                'Absolute Value Projected Score Error': 'Absolute Value Projected Score Error'
            })

            # Set the index to Manager
            aggregated_df.set_index('Manager', inplace=True)

            display_df = aggregated_df[['W', 'L', 'PF', 'PA', 'Projected PF', 'Projected Average', 'Expected Odds', 'Margin', 'Expected Margin', 'Projected W', 'Above Projected Score', 'W vs Spread', 'Projected Score Error', 'Absolute Value Projected Score Error']]
            st.dataframe(display_df)
        else:
            st.write("The required columns are not available in the data.")