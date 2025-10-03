import streamlit as st
import pandas as pd

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

            # Compute Sacko flag before aggregation
            sacko_flags = []
            if 'sacko' in self.df.columns:
                for (manager, year), group in self.df.groupby(['manager', 'year']):
                    sacko_flag = group['sacko'].eq(1).any()
                    sacko_flags.append({'manager': manager, 'year': year, 'sacko': sacko_flag})
            else:
                for (manager, year), group in self.df.groupby(['manager', 'year']):
                    sacko_flags.append({'manager': manager, 'year': year, 'sacko': False})
            sacko_df = pd.DataFrame(sacko_flags)

            # Only aggregate columns that exist in the DataFrame
            agg_columns = [
                'team_points', 'opponent_points', 'win', 'loss', 'quarterfinal', 'semifinal', 'championship',
                'champion', 'is_playoffs', 'margin', 'total_matchup_score', 'teams_beat_this_week',
                'opponent_teams_beat_this_week', 'close_margin', 'above_league_median', 'below_league_median',
                'above_opponent_median', 'below_opponent_median', 'gpa', 'real_score', 'real_opponent_points',
                'real_margin', 'real_total_matchup_score'
            ]
            agg_dict = {col: aggregation_func for col in agg_columns if col in self.df.columns}

            aggregated_df = self.df.groupby(['manager', 'year']).agg(agg_dict).reset_index()

            # Merge Sacko column
            aggregated_df = pd.merge(aggregated_df, sacko_df, on=['manager', 'year'], how='left')

            # Rounding
            if aggregation_type:
                columns_to_round_2 = [c for c in [
                    'team_points', 'opponent_points', 'margin', 'total_matchup_score', 'teams_beat_this_week',
                    'opponent_teams_beat_this_week', 'gpa', 'real_score', 'real_opponent_points', 'real_margin',
                    'real_total_matchup_score'
                ] if c in aggregated_df.columns]
                columns_to_round_3 = [c for c in [
                    'close_margin', 'above_league_median', 'below_league_median', 'above_opponent_median',
                    'below_opponent_median'
                ] if c in aggregated_df.columns]
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df[columns_to_round_3] = aggregated_df[columns_to_round_3].round(3)
                if 'win' in aggregated_df.columns:
                    aggregated_df['win'] = aggregated_df['win'].round(3)
                if 'loss' in aggregated_df.columns:
                    aggregated_df['loss'] = aggregated_df['loss'].round(3)

            aggregated_df['year'] = aggregated_df['year'].astype(str)

            # Playoff/Champ flags
            if 'quarterfinal' in aggregated_df.columns:
                aggregated_df['quarterfinal_check'] = aggregated_df['quarterfinal'] > 0
            if 'semifinal' in aggregated_df.columns:
                aggregated_df['semifinal_check'] = aggregated_df['semifinal'] > 0
            if 'championship' in aggregated_df.columns:
                aggregated_df['championship_check'] = aggregated_df['championship'] > 0
            if 'champion' in aggregated_df.columns:
                aggregated_df['champion_check'] = aggregated_df['champion'] > 0
            if 'is_playoffs' in aggregated_df.columns:
                aggregated_df['team_made_playoffs'] = aggregated_df['is_playoffs'] > 0

            # Display columns (only those that exist)
            display_cols = [
                'manager', 'year', 'win', 'loss', 'team_points', 'opponent_points', 'team_made_playoffs',
                'quarterfinal_check', 'semifinal_check', 'championship_check', 'champion_check', 'sacko'
            ]
            display_df = aggregated_df[[c for c in display_cols if c in aggregated_df.columns]]
            display_df = display_df.rename(columns={
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_points': 'PA',
                'team_made_playoffs': 'Playoffs',
                'quarterfinal_check': 'Quarterfinals',
                'semifinal_check': 'Semifinals',
                'championship_check': 'Championship',
                'champion_check': 'Champ',
                'sacko': 'Sacko'
            })
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column `win` is not available in the data.")