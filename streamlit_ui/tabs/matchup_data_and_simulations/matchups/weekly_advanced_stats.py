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
            display_df['year'] = display_df['year'].astype(str)
            display_df = display_df.sort_values(by=['year', 'week']).reset_index(drop=True)

            # Round specified columns to 2 digits
            columns_to_round = [
                'weekly_mean', 'weekly_median', 'League-Wide Season Mean', 'League-Wide Season Median',
                'Personal Season Mean', 'Personal Season Median'
            ]
            display_df[columns_to_round] = display_df[columns_to_round].round(2)

            # Convert specified columns to boolean
            columns_to_boolean = [
                'close_margin', 'above_league_median', 'below_league_median', 'Above Opponent Median', 'Below Opponent Median'
            ]
            display_df[columns_to_boolean] = display_df[columns_to_boolean].astype(bool)

            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required columns are not available in the data.")