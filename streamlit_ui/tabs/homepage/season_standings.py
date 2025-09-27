import streamlit as st
import pandas as pd

class SeasonStandingsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Season Standings")
        df = self.df
        if 'is_consolation' in df.columns:
            df = df[df['is_consolation'] != 1].copy()

        if all(col in df.columns for col in ['win', 'manager', 'year', 'team_name']):
            df['win'] = df['win'] == 1
            df['loss'] = df['win'] == 0

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            sacko_flags = []
            if 'sacko' in df.columns:
                for (manager, year), group in df.groupby(['manager', 'year']):
                    sacko_flag = group['sacko'].eq(1).any()
                    sacko_flags.append({'manager': manager, 'year': year, 'sacko': sacko_flag})
            else:
                for (manager, year), group in df.groupby(['manager', 'year']):
                    sacko_flags.append({'manager': manager, 'year': year, 'sacko': False})
            sacko_df = pd.DataFrame(sacko_flags)

            agg_dict = {
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'is_playoffs': aggregation_func,
                'quarterfinal': aggregation_func,
                'semifinal': aggregation_func,
                'championship': aggregation_func,
                'champion': aggregation_func,
                'team_name': 'first'
            }

            aggregated_df = df.groupby(['manager', 'year']).agg(agg_dict).reset_index()
            aggregated_df = pd.merge(aggregated_df, sacko_df, on=['manager', 'year'], how='left')

            if 'final_playoff_seed' in df.columns:
                seed_df = df[['manager', 'year', 'final_playoff_seed']].drop_duplicates(subset=['manager', 'year'])
                aggregated_df = pd.merge(aggregated_df, seed_df, on=['manager', 'year'], how='left')

            if aggregation_type:
                columns_to_round_2 = ['team_points', 'opponent_score']
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            aggregated_df['year'] = aggregated_df['year'].astype(str)

            years_with_champion = set(df[df['champion'] == 1]['year'].astype(str).unique())
            all_years = set(aggregated_df['year'].unique())
            in_progress_years = all_years - years_with_champion

            def get_final_result(row):
                if row['year'] in in_progress_years:
                    return "Season in Progress"
                if row.get('sacko', False):
                    return "Sacko"
                if row.get('champion', 0) > 0:
                    return "Champion"
                if row.get('championship', 0) > 0:
                    return "Lost in Championship"
                if row.get('semifinal', 0) > 0:
                    return "Lost in Semifinals"
                if row.get('quarterfinal', 0) > 0:
                    return "Lost in Quarterfinals"
                if row.get('is_playoffs', 0) > 0:
                    return "Missed Playoffs"
                return "Missed Playoffs"

            aggregated_df['Final Result'] = aggregated_df.apply(get_final_result, axis=1)

            display_columns = ['final_playoff_seed', 'manager', 'team_name', 'year', 'win', 'loss', 'team_points', 'opponent_score', 'Final Result'] \
                if 'final_playoff_seed' in aggregated_df.columns else \
                ['manager', 'team_name', 'year', 'win', 'loss', 'team_points', 'opponent_score', 'Final Result']

            display_df = aggregated_df[display_columns]
            display_df = display_df.rename(columns={
                'final_playoff_seed': 'Seed',
                'manager': 'Manager',
                'team_name': 'Team',
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA'
            })

            years = sorted(display_df['Year'].unique())
            selected_year = st.selectbox("Select Year", years, index=len(years)-1, key=f"{prefix}_year")
            filtered_df = display_df[display_df['Year'] == selected_year]
            if 'Seed' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('Seed', ascending=True)
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

def display_season_standings(df, prefix=""):
    viewer = SeasonStandingsViewer(df)
    viewer.display(prefix)