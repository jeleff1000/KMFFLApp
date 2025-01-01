import streamlit as st

class CareerMatchupStatsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Career Matchup Stats")
        if 'win' in self.df.columns:
            self.df['win'] = self.df['win'] == 1
            self.df['loss'] = self.df['win'] == 0

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'sum'  # Always use sum for aggregation

            # Calculate the count of unique years and weeks for each manager
            self.df['ManagerYearWeek'] = self.df['Manager'] + self.df['year'].astype(str) + self.df['week'].astype(str)
            unique_years = self.df.groupby('Manager')['year'].nunique()
            unique_manager_weeks = self.df.groupby('Manager')['ManagerYearWeek'].nunique()
            self.df['unique_years'] = self.df['Manager'].map(unique_years)
            self.df['unique_manager_weeks'] = self.df['Manager'].map(unique_manager_weeks)

            champion_count = self.df.groupby(['Manager', 'year'])['Champion'].max().groupby('Manager').sum()
            playoffs_count = self.df.groupby(['Manager', 'year'])['is_playoffs'].max().groupby('Manager').sum()
            quarterfinal_count = self.df.groupby(['Manager', 'year'])['quarterfinal'].max().groupby('Manager').sum()
            semifinal_count = self.df.groupby(['Manager', 'year'])['semifinal'].max().groupby('Manager').sum()
            championship_count = self.df.groupby(['Manager', 'year'])['championship'].max().groupby('Manager').sum()

            aggregated_df = self.df.groupby('Manager').agg({
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
                'Real Score': aggregation_func,
                'Real Opponent Score': aggregation_func,
                'Real Margin': aggregation_func,
                'Real Total Matchup Score': aggregation_func,
                'unique_years': 'first',  # Include the unique year count
                'unique_manager_weeks': 'first'  # Include the unique manager week count
            }).reset_index()

            # Add the calculated counts to the aggregated DataFrame
            aggregated_df['Champion'] = champion_count.values
            aggregated_df['is_playoffs'] = playoffs_count.values
            aggregated_df['quarterfinal'] = quarterfinal_count.values
            aggregated_df['semifinal'] = semifinal_count.values
            aggregated_df['championship'] = championship_count.values

            if aggregation_type:
                aggregated_df['Champion'] = aggregated_df['Champion'] / aggregated_df['unique_years']
                aggregated_df['is_playoffs'] = aggregated_df['is_playoffs'] / aggregated_df['unique_years']
                aggregated_df['quarterfinal'] = aggregated_df['quarterfinal'] / aggregated_df['unique_years']
                aggregated_df['semifinal'] = aggregated_df['semifinal'] / aggregated_df['unique_years']
                aggregated_df['championship'] = aggregated_df['championship'] / aggregated_df['unique_years']

                # Average other values per game
                columns_to_average = [
                    'team_points', 'opponent_score', 'win', 'loss', 'margin', 'total_matchup_score',
                    'teams_beat_this_week', 'opponent_teams_beat_this_week', 'close_margin',
                    'above_league_median', 'below_league_median', 'Above Opponent Median',
                    'Below Opponent Median', 'Real Score', 'Real Opponent Score', 'Real Margin',
                    'Real Total Matchup Score'
                ]
                aggregated_df[columns_to_average] = aggregated_df[columns_to_average].div(aggregated_df['unique_manager_weeks'], axis=0)

            columns_to_round_2 = [
                'team_points', 'opponent_score', 'margin', 'total_matchup_score', 'teams_beat_this_week',
                'opponent_teams_beat_this_week', 'Real Score', 'Real Opponent Score', 'Real Margin',
                'Real Total Matchup Score'
            ]
            columns_to_round_3 = [
                'close_margin', 'above_league_median', 'below_league_median', 'Above Opponent Median',
                'Below Opponent Median', 'quarterfinal', 'semifinal', 'championship', 'Champion', 'is_playoffs'
            ]
            aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
            aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
            aggregated_df['win'] = aggregated_df['win'].round(3)
            aggregated_df['loss'] = aggregated_df['loss'].round(3)
            aggregated_df['GPA'] = aggregated_df['GPA'].round(2)

            # Set the index to Manager
            aggregated_df.set_index('Manager', inplace=True)

            display_df = aggregated_df[['win', 'loss', 'team_points', 'opponent_score', 'quarterfinal', 'semifinal', 'championship', 'Champion', 'is_playoffs', 'margin', 'total_matchup_score', 'teams_beat_this_week', 'opponent_teams_beat_this_week', 'close_margin', 'above_league_median', 'below_league_median', 'Above Opponent Median', 'Below Opponent Median', 'GPA', 'Real Score', 'Real Opponent Score', 'Real Margin', 'Real Total Matchup Score']]
            st.dataframe(display_df)
        else:
            st.write("The required column 'win' is not available in the data.")