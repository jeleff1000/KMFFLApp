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
            aggregation_func = 'sum'

            self.df['manager_year_week'] = self.df['manager'] + self.df['year'].astype(str) + self.df['week'].astype(str)
            unique_years = self.df.groupby('manager')['year'].nunique()
            unique_manager_weeks = self.df.groupby('manager')['manager_year_week'].nunique()
            self.df['unique_years'] = self.df['manager'].map(unique_years)
            self.df['unique_manager_weeks'] = self.df['manager'].map(unique_manager_weeks)

            champion_count = self.df.groupby(['manager', 'year'])['champion'].max().groupby('manager').sum() if 'champion' in self.df.columns else None
            sacko_count = self.df.groupby(['manager', 'year'])['sacko'].max().groupby('manager').sum() if 'sacko' in self.df.columns else None
            playoffs_count = self.df.groupby(['manager', 'year'])['is_playoffs'].max().groupby('manager').sum() if 'is_playoffs' in self.df.columns else None
            quarterfinal_count = self.df.groupby(['manager', 'year'])['quarterfinal'].max().groupby('manager').sum() if 'quarterfinal' in self.df.columns else None
            semifinal_count = self.df.groupby(['manager', 'year'])['semifinal'].max().groupby('manager').sum() if 'semifinal' in self.df.columns else None
            championship_count = self.df.groupby(['manager', 'year'])['championship'].max().groupby('manager').sum() if 'championship' in self.df.columns else None

            agg_dict = {
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'unique_years': 'first',
                'unique_manager_weeks': 'first'
            }
            agg_dict = {k: v for k, v in agg_dict.items() if k in self.df.columns}
            aggregated_df = self.df.groupby('manager').agg(agg_dict).reset_index()

            if champion_count is not None:
                aggregated_df['champion'] = champion_count.values
            if sacko_count is not None:
                aggregated_df['sacko'] = sacko_count.values
            if playoffs_count is not None:
                aggregated_df['is_playoffs'] = playoffs_count.values
            if quarterfinal_count is not None:
                aggregated_df['quarterfinal'] = quarterfinal_count.values
            if semifinal_count is not None:
                aggregated_df['semifinal'] = semifinal_count.values
            if championship_count is not None:
                aggregated_df['championship'] = championship_count.values

            if aggregation_type:
                if 'champion' in aggregated_df.columns:
                    aggregated_df['champion'] = aggregated_df['champion'] / aggregated_df['unique_years']
                if 'sacko' in aggregated_df.columns:
                    aggregated_df['sacko'] = aggregated_df['sacko'] / aggregated_df['unique_years']
                if 'is_playoffs' in aggregated_df.columns:
                    aggregated_df['is_playoffs'] = aggregated_df['is_playoffs'] / aggregated_df['unique_years']
                if 'quarterfinal' in aggregated_df.columns:
                    aggregated_df['quarterfinal'] = aggregated_df['quarterfinal'] / aggregated_df['unique_years']
                if 'semifinal' in aggregated_df.columns:
                    aggregated_df['semifinal'] = aggregated_df['semifinal'] / aggregated_df['unique_years']
                if 'championship' in aggregated_df.columns:
                    aggregated_df['championship'] = aggregated_df['championship'] / aggregated_df['unique_years']

                columns_to_average = [
                    'team_points', 'opponent_score', 'win', 'loss'
                ]
                for col in columns_to_average:
                    if col in aggregated_df.columns:
                        aggregated_df[col] = aggregated_df[col] / aggregated_df['unique_manager_weeks']

            columns_to_round_2 = [c for c in ['team_points', 'opponent_score'] if c in aggregated_df.columns]
            columns_to_round_3 = [c for c in ['quarterfinal', 'semifinal', 'championship', 'champion', 'is_playoffs', 'sacko'] if c in aggregated_df.columns]
            if columns_to_round_2:
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
            if columns_to_round_3:
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
            if 'win' in aggregated_df.columns:
                aggregated_df['win'] = aggregated_df['win'].round(3)
            if 'loss' in aggregated_df.columns:
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            rename_dict = {
                'manager': 'Manager',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA',
                'quarterfinal': 'Quarterfinals',
                'semifinal': 'Semifinals',
                'championship': 'Finals',
                'champion': 'Championships',
                'is_playoffs': 'Playoffs',
                'sacko': 'Sackos'
            }
            aggregated_df = aggregated_df.rename(columns=rename_dict)

            columns = ['Manager', 'W', 'L', 'PF', 'PA']
            if 'Playoffs' in aggregated_df.columns:
                columns.append('Playoffs')
            if 'Quarterfinals' in aggregated_df.columns:
                columns.append('Quarterfinals')
            if 'Semifinals' in aggregated_df.columns:
                columns.append('Semifinals')
            if 'Finals' in aggregated_df.columns:
                columns.append('Finals')
            if 'Championships' in aggregated_df.columns:
                columns.append('Championships')
            if 'Sackos' in aggregated_df.columns:
                columns.append('Sackos')
            display_df = aggregated_df[columns]
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column `win` is not available in the data.")