import streamlit as st

class SeasonMatchupStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Season Matchup Stats")
        if 'win' in self.df.columns:
            self.df['win'] = self.df['win'] == 1
            self.df['loss'] = self.df['win'] == 0

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = self.df.groupby(['Manager', 'year']).agg({
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'quarterfinal': aggregation_func,
                'semifinal': aggregation_func,
                'championship': aggregation_func,
                'Champion': aggregation_func,
                'is_playoffs': aggregation_func,
                'margin': aggregation_func,
                'total_matchup_score': aggregation_func,
                'teams_beat_this_week': aggregation_func,
                'opponent_teams_beat_this_week': aggregation_func,
                'close_margin': aggregation_func,
                'above_league_median': aggregation_func,
                'below_league_median': aggregation_func,
                'Above Opponent Median': aggregation_func,
                'Below Opponent Median': aggregation_func,
                'GPA': aggregation_func,
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

            aggregated_df['quarterfinal_check'] = aggregated_df['quarterfinal'] > 0
            aggregated_df['semifinal_check'] = aggregated_df['semifinal'] > 0
            aggregated_df['championship_check'] = aggregated_df['championship'] > 0
            aggregated_df['Champion_check'] = aggregated_df['Champion'] > 0
            aggregated_df['Team_Made_Playoffs'] = aggregated_df['is_playoffs'] > 0

            display_df = aggregated_df[['Manager', 'year', 'win', 'loss', 'team_points', 'opponent_score', 'Team_Made_Playoffs', 'quarterfinal_check', 'semifinal_check', 'championship_check', 'Champion_check']]
            display_df = display_df.rename(columns={
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA',
                'Team_Made_Playoffs': 'Playoffs',
                'quarterfinal_check': 'Quarterfinals',
                'semifinal_check': 'Semifinals',
                'championship_check': 'Championship',
                'Champion_check': 'Champ'
            })
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column 'win' is not available in the data.")