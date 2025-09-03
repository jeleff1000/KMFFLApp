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
            sacko_count = self.df.groupby(['Manager', 'year'])['Sacko'].max().groupby('Manager').sum() if 'Sacko' in self.df.columns else None
            playoffs_count = self.df.groupby(['Manager', 'year'])['is_playoffs'].max().groupby('Manager').sum()
            quarterfinal_count = self.df.groupby(['Manager', 'year'])['quarterfinal'].max().groupby('Manager').sum()
            semifinal_count = self.df.groupby(['Manager', 'year'])['semifinal'].max().groupby('Manager').sum()
            championship_count = self.df.groupby(['Manager', 'year'])['championship'].max().groupby('Manager').sum()

            aggregated_df = self.df.groupby('Manager').agg({
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'unique_years': 'first',
                'unique_manager_weeks': 'first'
            }).reset_index()

            # Add the calculated counts to the aggregated DataFrame
            aggregated_df['Champion'] = champion_count.values
            if sacko_count is not None:
                aggregated_df['Sacko'] = sacko_count.values
            aggregated_df['is_playoffs'] = playoffs_count.values
            aggregated_df['quarterfinal'] = quarterfinal_count.values
            aggregated_df['semifinal'] = semifinal_count.values
            aggregated_df['championship'] = championship_count.values

            if aggregation_type:
                aggregated_df['Champion'] = aggregated_df['Champion'] / aggregated_df['unique_years']
                if sacko_count is not None:
                    aggregated_df['Sacko'] = aggregated_df['Sacko'] / aggregated_df['unique_years']
                aggregated_df['is_playoffs'] = aggregated_df['is_playoffs'] / aggregated_df['unique_years']
                aggregated_df['quarterfinal'] = aggregated_df['quarterfinal'] / aggregated_df['unique_years']
                aggregated_df['semifinal'] = aggregated_df['semifinal'] / aggregated_df['unique_years']
                aggregated_df['championship'] = aggregated_df['championship'] / aggregated_df['unique_years']

                columns_to_average = [
                    'team_points', 'opponent_score', 'win', 'loss'
                ]
                aggregated_df[columns_to_average] = aggregated_df[columns_to_average].div(aggregated_df['unique_manager_weeks'], axis=0)

            columns_to_round_2 = [
                'team_points', 'opponent_score'
            ]
            columns_to_round_3 = [
                'quarterfinal', 'semifinal', 'championship', 'Champion', 'is_playoffs'
            ]
            if sacko_count is not None:
                columns_to_round_3.append('Sacko')
            aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
            aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
            aggregated_df['win'] = aggregated_df['win'].round(3)
            aggregated_df['loss'] = aggregated_df['loss'].round(3)

            # Rename columns
            rename_dict = {
                'Manager': 'Manager',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA',
                'quarterfinal': 'Quarterfinals',
                'semifinal': 'Semifinals',
                'championship': 'Finals',
                'Champion': 'Championships',
                'is_playoffs': 'Playoffs'
            }
            if sacko_count is not None:
                rename_dict['Sacko'] = 'Sackos'
            aggregated_df = aggregated_df.rename(columns=rename_dict)

            # Reorder columns
            columns = ['Manager', 'W', 'L', 'PF', 'PA', 'Playoffs', 'Quarterfinals', 'Semifinals', 'Finals', 'Championships']
            if sacko_count is not None:
                columns.append('Sackos')
            display_df = aggregated_df[columns]
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column 'win' is not available in the data.")