import streamlit as st

class WeeklyProjectedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Weekly Projected Stats")
        required_columns = ['Manager', 'opponent', 'team_points', 'opponent_score', 'team_projected_points',
                            'opponent_projected_points', 'Expected Odds', 'margin', 'Expected Spread', 'week', 'year',
                            'Projected Score Error', 'Absolute Value Projected Score Error']
        if all(col in self.df.columns for col in required_columns):
            self.df['win'] = self.df['team_points'] > self.df['opponent_score']
            self.df['Projected Wins'] = self.df['team_projected_points'] > self.df['opponent_projected_points']
            self.df['Above Projected Score'] = self.df['team_points'] > self.df['team_projected_points']
            self.df['Win Matchup Against the Spread'] = (self.df['team_points'] - self.df['opponent_score']) > self.df['Expected Spread']

            display_df = self.df[['Manager', 'week', 'year', 'opponent', 'team_points', 'opponent_score', 'team_projected_points',
                                  'opponent_projected_points', 'Expected Odds', 'margin', 'Expected Spread',
                                  'win', 'Projected Wins', 'Above Projected Score', 'Win Matchup Against the Spread',
                                  'Projected Score Error', 'Absolute Value Projected Score Error']]
            display_df['year'] = display_df['year'].apply(lambda x: f"{x:.0f}")
            display_df = display_df.sort_values(by=['year', 'week']).reset_index(drop=True)
            st.dataframe(display_df, hide_index=True, use_container_width=True, column_config={"Manager": {"frozen": True}, "week": {"frozen": True}, "year": {"frozen": True}})
        else:
            st.write("The required columns are not available in the data.")