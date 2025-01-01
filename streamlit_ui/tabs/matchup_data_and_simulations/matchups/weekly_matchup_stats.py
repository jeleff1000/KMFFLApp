import streamlit as st

class WeeklyMatchupStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Weekly Matchup Stats")
        if 'win' in self.df.columns:
            self.df['win'] = self.df['win'] == 1
            self.df['is_playoffs_check'] = self.df['is_playoffs'] == 1
            display_df = self.df[['Manager', 'week', 'year', 'opponent', 'team_points', 'opponent_score', 'win', 'is_playoffs_check']]
            display_df['year'] = display_df['year'].astype(str)
            display_df = display_df.sort_values(by=['year', 'week']).reset_index(drop=True)
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column 'win' is not available in the data.")