import streamlit as st

class WeeklyMatchupStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Weekly Matchup Stats")
        if 'win' in self.df.columns:
            self.df['win'] = self.df['win'] == 1
            self.df['is_playoffs_check'] = self.df['is_playoffs'] == 1
            display_df = self.df[['manager', 'week', 'year', 'opponent', 'team_points', 'opponent_points', 'win', 'is_playoffs_check']]
            display_df = display_df.rename(columns={
                'manager': 'manager',
                'week': 'Week',
                'year': 'Year',
                'opponent': 'Opponent',
                'team_points': 'Team Points',
                'opponent_points': 'Opp Pts',
                'win': 'Win',
                'is_playoffs_check': 'Playoff Game'
            })
            display_df['Year'] = display_df['Year'].astype(str)
            display_df = display_df.sort_values(by=['Year', 'Week']).reset_index(drop=True)
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column 'win' is not available in the data.")