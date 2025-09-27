import streamlit as st

class WeeklyAdvancedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Weekly Advanced Stats")
        required_columns = [
            'manager', 'week', 'year', 'opponent', 'team_points', 'opponent_score', 'win', 'is_playoffs',
            'margin', 'weekly_mean', 'weekly_median', 'total_matchup_score', 'teams_beat_this_week',
            'opponent_teams_beat_this_week', 'close_margin', 'above_league_median', 'below_league_median',
            'above_opponent_median', 'below_opponent_median', 'grade', 'gpa', 'league_weekly_mean',
            'league_weekly_median', 'personal_season_mean', 'personal_season_median', 'winning_streak',
            'losing_streak', 'real_score', 'real_opponent_score', 'real_margin', 'real_total_matchup_score'
        ]

        if all(col in self.df.columns for col in required_columns):
            display_df = self.df[required_columns]
            display_df = display_df.rename(columns={
                'week': 'Week',
                'year': 'Year',
                'manager': 'Manager',
                'opponent': 'Opponent',
                'team_points': 'Team Points',
                'opponent_score': 'Opp Pts',
                'win': 'Win',
                'is_playoffs': 'Playoff Game',
                'margin': 'Margin',
                'weekly_mean': 'Weekly Mean',
                'weekly_median': 'Weekly Median',
                'total_matchup_score': 'Total Matchup Score',
                'teams_beat_this_week': 'Teams Beat this Week',
                'opponent_teams_beat_this_week': 'Opponent Teams Beat this Week',
                'close_margin': 'Close Margin',
                'above_league_median': 'Above League Median',
                'below_league_median': 'Below League',
                'above_opponent_median': 'Above Opponent Median',
                'below_opponent_median': 'Below Opponent Median',
                'grade': 'Grade',
                'gpa': 'GPA',
                'league_weekly_mean': 'League-Wide Season Mean',
                'league_weekly_median': 'League-Wide Season Median',
                'personal_season_mean': 'Personal Season Mean',
                'personal_season_median': 'Personal Season Median',
                'winning_streak': 'Winning Streak',
                'losing_streak': 'Losing Streak',
                'real_score': 'Real Score',
                'real_opponent_score': 'Real Opponent Score',
                'real_margin': 'Real Margin',
                'real_total_matchup_score': 'Real Total Matchup Score'
            })
            display_df['Year'] = display_df['Year'].astype(str)
            display_df = display_df.sort_values(by=['Year', 'Week']).reset_index(drop=True)

            columns_to_round = [
                'Weekly Mean', 'Weekly Median', 'League-Wide Season Mean', 'League-Wide Season Median',
                'Personal Season Mean', 'Personal Season Median'
            ]
            display_df[columns_to_round] = display_df[columns_to_round].round(2)

            columns_to_boolean = [
                'Close Margin', 'Above League Median', 'Below League', 'Above Opponent Median', 'Below Opponent Median'
            ]
            display_df[columns_to_boolean] = display_df[columns_to_boolean].astype(bool)

            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required columns are not available in the data.")