import streamlit as st

class SeasonAdvancedStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Season Advanced Stats")
        required_columns = [
            'Manager', 'opponent', 'week', 'year', 'team_points', 'opponent_score', 'win',
            'margin', 'total_matchup_score', 'teams_beat_this_week', 'opponent_teams_beat_this_week',
            'close_margin', 'above_league_median', 'below_league_median', 'Above Opponent Median',
            'Below Opponent Median', 'GPA', 'League-Wide Season Mean', 'League-Wide Season Median',
            'Personal Season Mean', 'Personal Season Median', 'Winning Streak', 'Losing Streak',
            'Real Score', 'Real Opponent Score', 'Real Margin', 'Real Total Matchup Score'
        ]

        available_columns = self.df.columns.tolist()
        missing_columns = [col for col in required_columns if col not in available_columns]

        if missing_columns:
            st.write(f"The required columns are not available in the data: {missing_columns}")
            st.write(f"Available columns: {available_columns}")
        else:
            self.df['loss'] = self.df['team_points'] <= self.df['opponent_score']

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = self.df.groupby(['Manager', 'year']).agg({
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'margin': aggregation_func,
                'total_matchup_score': aggregation_func,
                'teams_beat_this_week': aggregation_func,
                'opponent_teams_beat_this_week': aggregation_func,
                'close_margin': aggregation_func,
                'above_league_median': aggregation_func,
                'below_league_median': aggregation_func,
                'Above Opponent Median': aggregation_func,
                'Below Opponent Median': aggregation_func,
                'GPA': 'mean',
                'League-Wide Season Mean': 'mean',
                'League-Wide Season Median': 'median',
                'Personal Season Mean': 'mean',
                'Personal Season Median': 'median',
                'Winning Streak': 'max',
                'Losing Streak': 'max',
                'Real Score': aggregation_func,
                'Real Opponent Score': aggregation_func,
                'Real Margin': aggregation_func,
                'Real Total Matchup Score': aggregation_func
            }).reset_index()

            if aggregation_type:
                columns_to_round_2 = [
                    'team_points', 'opponent_score', 'margin', 'total_matchup_score', 'teams_beat_this_week',
                    'opponent_teams_beat_this_week', 'GPA', 'Real Score', 'Real Opponent Score', 'Real Margin',
                    'Real Total Matchup Score'
                ]
                columns_to_round_3 = [
                    'close_margin', 'above_league_median', 'below_league_median', 'Above Opponent Median',
                    'Below Opponent Median'
                ]
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            aggregated_df['year'] = aggregated_df['year'].astype(str)

            display_df = aggregated_df.sort_values(by=['Manager', 'year']).reset_index(drop=True)

            # Round specified columns to 2 digits
            columns_to_round = [
                'League-Wide Season Mean', 'League-Wide Season Median', 'Personal Season Mean',
                'Personal Season Median', 'GPA'
            ]
            display_df[columns_to_round] = display_df[columns_to_round].round(2)

            display_df = display_df.rename(columns={
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA',
                'margin': 'Margin',
                'total_matchup_score': 'Matchup Score',
                'teams_beat_this_week': 'W Vs Every Tm',
                'opponent_teams_beat_this_week': 'Opp W Vs Every Tm',
                'close_margin': 'Close Margin',
                'above_league_median': 'Above Lg Mean',
                'below_league_median': 'Above Lg Median',
                'Above Opponent Median': 'Above Opp Median',
                'Below Opponent Median': 'Below Opp Median',
                'GPA': 'GPA',
                'League-Wide Season Mean': 'League-Wide Season Mean',
                'League-Wide Season Median': 'League-Wide Season Median',
                'Personal Season Mean': 'Team Mean',
                'Personal Season Median': 'Team Median',
                'Winning Streak': 'Winning Streak',
                'Losing Streak': 'Losing Streak',
                'Real Score': 'Real Points',
                'Real Opponent Score': 'Real Opp score',
                'Real Margin': 'Real Margin',
                'Real Total Matchup Score': 'Real Matchup Score'
            })

            st.dataframe(display_df, hide_index=True)