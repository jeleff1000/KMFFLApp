import streamlit as st

class SeasonAdvancedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Career Advanced Stats")
        required_columns = [
            'manager', 'opponent', 'week', 'year', 'team_points', 'opponent_points', 'win',
            'margin', 'total_matchup_score', 'teams_beat_this_week', 'opponent_teams_beat_this_week',
            'close_margin', 'above_league_median', 'below_league_median', 'above_opponent_median',
            'below_opponent_median', 'gpa', 'league_weekly_mean', 'league_weekly_median',
            'personal_season_mean', 'personal_season_median', 'winning_streak', 'losing_streak',
            'real_score', 'real_opponent_points', 'real_margin', 'real_total_matchup_score'
        ]

        available_columns = self.df.columns.tolist()
        missing_columns = [col for col in required_columns if col not in available_columns]

        if missing_columns:
            st.write(f"The required columns are not available in the data: {missing_columns}")
            st.write(f"Available columns: {available_columns}")
        else:
            self.df['loss'] = self.df['team_points'] <= self.df['opponent_points']

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = self.df.groupby('manager').agg({
                'team_points': aggregation_func,
                'opponent_points': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'margin': aggregation_func,
                'total_matchup_score': aggregation_func,
                'teams_beat_this_week': aggregation_func,
                'opponent_teams_beat_this_week': aggregation_func,
                'close_margin': aggregation_func,
                'above_league_median': aggregation_func,
                'below_league_median': aggregation_func,
                'above_opponent_median': aggregation_func,
                'below_opponent_median': aggregation_func,
                'gpa': 'mean',
                'league_weekly_mean': 'mean',
                'league_weekly_median': 'median',
                'personal_season_mean': 'mean',
                'personal_season_median': 'median',
                'winning_streak': 'max',
                'losing_streak': 'max',
                'real_score': aggregation_func,
                'real_opponent_points': aggregation_func,
                'real_margin': aggregation_func,
                'real_total_matchup_score': aggregation_func
            }).reset_index()

            if aggregation_type:
                columns_to_round_2 = [
                    'team_points', 'opponent_points', 'margin', 'total_matchup_score', 'teams_beat_this_week',
                    'opponent_teams_beat_this_week', 'gpa', 'real_score', 'real_opponent_points', 'real_margin',
                    'real_total_matchup_score'
                ]
                columns_to_round_3 = [
                    'close_margin', 'above_league_median', 'below_league_median', 'above_opponent_median',
                    'below_opponent_median'
                ]
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            # Rename columns
            aggregated_df = aggregated_df.rename(columns={
                'manager': 'Manager',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_points': 'PA',
                'margin': 'Margin',
                'total_matchup_score': 'Total Matchup Score',
                'teams_beat_this_week': 'W Vs Every Tm',
                'opponent_teams_beat_this_week': 'Opp W Vs Every Team',
                'close_margin': 'Close Margin',
                'above_league_median': 'Above Lg Median',
                'below_league_median': 'Below League Median',
                'above_opponent_median': 'Above Opp Median',
                'below_opponent_median': 'Below Opp Median',
                'gpa': 'GPA',
                'league_weekly_mean': 'League-Wide Season Mean',
                'league_weekly_median': 'League-Wide Season Median',
                'personal_season_mean': 'Personal Team Mean',
                'personal_season_median': 'Personal Team Median',
                'winning_streak': 'Max W Streak',
                'losing_streak': 'Max L Streak',
                'real_score': 'Real Score',
                'real_opponent_points': 'Real Opp Score',
                'real_margin': 'Real Margin',
                'real_total_matchup_score': 'Real Total Matchup Score'
            })

            aggregated_df.set_index('Manager', inplace=True)

            columns_to_round = [
                'League-Wide Season Mean', 'League-Wide Season Median', 'Personal Team Mean',
                'Personal Team Median', 'GPA'
            ]
            aggregated_df[columns_to_round] = aggregated_df[columns_to_round].round(2)

            display_df = aggregated_df[['W', 'L', 'PF', 'PA', 'Margin', 'Total Matchup Score', 'W Vs Every Tm', 'Opp W Vs Every Team', 'Close Margin', 'Above Lg Median', 'Below League Median', 'Above Opp Median', 'Below Opp Median', 'GPA', 'League-Wide Season Mean', 'League-Wide Season Median', 'Personal Team Mean', 'Personal Team Median', 'Max W Streak', 'Max L Streak', 'Real Score', 'Real Opp Score', 'Real Margin', 'Real Total Matchup Score']]

            st.dataframe(display_df, hide_index=True)