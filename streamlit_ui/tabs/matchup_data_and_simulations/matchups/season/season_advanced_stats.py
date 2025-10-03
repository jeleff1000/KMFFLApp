import streamlit as st

class SeasonAdvancedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Season Advanced Stats")
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

            aggregated_df = self.df.groupby(['manager', 'year']).agg({
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

            aggregated_df['year'] = aggregated_df['year'].astype(str)

            display_df = aggregated_df.sort_values(by=['manager', 'year']).reset_index(drop=True)

            columns_to_round = [
                'league_weekly_mean', 'league_weekly_median', 'personal_season_mean',
                'personal_season_median', 'gpa'
            ]
            display_df[columns_to_round] = display_df[columns_to_round].round(2)

            display_df = display_df.rename(columns={
                'manager': 'Manager',
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_points': 'PA',
                'margin': 'Margin',
                'total_matchup_score': 'Matchup Score',
                'teams_beat_this_week': 'W Vs Every Tm',
                'opponent_teams_beat_this_week': 'Opp W Vs Every Tm',
                'close_margin': 'Close Margin',
                'above_league_median': 'Above Lg Mean',
                'below_league_median': 'Below Lg Median',
                'above_opponent_median': 'Above Opp Median',
                'below_opponent_median': 'Below Opp Median',
                'gpa': 'GPA',
                'league_weekly_mean': 'League-Wide Season Mean',
                'league_weekly_median': 'League-Wide Season Median',
                'personal_season_mean': 'Team Mean',
                'personal_season_median': 'Team Median',
                'winning_streak': 'Winning Streak',
                'losing_streak': 'Losing Streak',
                'real_score': 'Real Points',
                'real_opponent_points': 'Real Opp score',
                'real_margin': 'Real Margin',
                'real_total_matchup_score': 'Real Matchup Score'
            })

            st.dataframe(display_df, hide_index=True)