import streamlit as st

class WeeklyAdvancedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Weekly Advanced Stats")
        required_columns = [
            'Manager', 'week', 'year', 'opponent', 'team_points', 'opponent_score', 'win', 'is_playoffs_check',
            'margin', 'weekly_mean', 'weekly_median', 'total_matchup_score', 'teams_beat_this_week',
            'opponent_teams_beat_this_week', 'close_margin', 'above_league_median', 'below_league_median',
            'Above Opponent Median', 'Below Opponent Median', 'grade', 'GPA', 'League-Wide Season Mean',
            'League-Wide Season Median', 'Personal Season Mean', 'Personal Season Median', 'Winning Streak',
            'Losing Streak', 'Real Score', 'Real Opponent Score', 'Real Margin', 'Real Total Matchup Score'
        ]

        if all(col in self.df.columns for col in required_columns):
            display_df = self.df[required_columns]
            display_df = display_df.rename(columns={
                'week': 'Week',
                'year': 'Year',
                'opponent': 'Opponent',
                'team_points': 'Team Points',
                'opponent_score': 'Opp Pts',
                'win': 'Win',
                'is_playoffs_check': 'Playoff Game',
                'margin': 'Margin',
                'weekly_mean': 'Weekly Mean',
                'weekly_median': 'Weekly Median',
                'total_matchup_score': 'Total Matchup Score',
                'teams_beat_this_week': 'Teams Beat this Week',
                'opponent_teams_beat_this_week': 'Opponent Teams Beat this Week',
                'close_margin': 'Close Margin',
                'above_league_median': 'Above League Median',
                'below_league_median': 'Below League',
                'Above Opponent Median': 'Above Opponent Median',
                'Below Opponent Median': 'Below Opponent Median',
                'grade': 'Grade',
                'GPA': 'GPA',
                'League-Wide Season Mean': 'League-Wide Season Mean',
                'League-Wide Season Median': 'League-Wide Season Median',
                'Personal Season Mean': 'Personal Season Mean',
                'Personal Season Median': 'Personal Season Median',
                'Winning Streak': 'Winning Streak',
                'Losing Streak': 'Losing Streak',
                'Real Score': 'Real Score',
                'Real Opponent Score': 'Real Opponent Score',
                'Real Margin': 'Real Margin',
                'Real Total Matchup Score': 'Real Total Matchup Score'
            })
            display_df['Year'] = display_df['Year'].astype(str)
            display_df = display_df.sort_values(by=['Year', 'Week']).reset_index(drop=True)

            # Round specified columns to 2 digits
            columns_to_round = [
                'Weekly Mean', 'Weekly Median', 'League-Wide Season Mean', 'League-Wide Season Median',
                'Personal Season Mean', 'Personal Season Median'
            ]
            display_df[columns_to_round] = display_df[columns_to_round].round(2)

            # Convert specified columns to boolean
            columns_to_boolean = [
                'Close Margin', 'Above League Median', 'Below League', 'Above Opponent Median', 'Below Opponent Median'
            ]
            display_df[columns_to_boolean] = display_df[columns_to_boolean].astype(bool)

            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required columns are not available in the data.")