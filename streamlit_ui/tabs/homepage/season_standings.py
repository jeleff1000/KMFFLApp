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

        if 'win' in df.columns:
            df['win'] = df['win'] == 1
            df['loss'] = df['win'] == 0

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            sacko_flags = []
            if 'Sacko' in df.columns:
                for (manager, year), group in df.groupby(['Manager', 'year']):
                    sacko_flag = group['Sacko'].eq(1).any()
                    sacko_flags.append({'Manager': manager, 'year': year, 'Sacko': sacko_flag})
            else:
                for (manager, year), group in df.groupby(['Manager', 'year']):
                    sacko_flags.append({'Manager': manager, 'year': year, 'Sacko': False})
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
                'Champion': aggregation_func
            }

            aggregated_df = df.groupby(['Manager', 'year']).agg(agg_dict).reset_index()
            aggregated_df = pd.merge(aggregated_df, sacko_df, on=['Manager', 'year'], how='left')

            if 'Final Playoff Seed' in df.columns:
                seed_df = df[['Manager', 'year', 'Final Playoff Seed']].drop_duplicates(subset=['Manager', 'year'])
                aggregated_df = pd.merge(aggregated_df, seed_df, on=['Manager', 'year'], how='left')

            if aggregation_type:
                columns_to_round_2 = ['team_points', 'opponent_score']
                aggregated_df[columns_to_round_2] = aggregated_df[columns_to_round_2].round(2)
                aggregated_df['win'] = aggregated_df['win'].round(3)
                aggregated_df['loss'] = aggregated_df['loss'].round(3)

            aggregated_df['year'] = aggregated_df['year'].astype(str)

            def get_final_result(row):
                if row.get('Sacko', False):
                    return "Sacko"
                if row.get('Champion', 0) > 0:
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

            display_columns = ['Final Playoff Seed', 'Manager', 'year', 'win', 'loss', 'team_points', 'opponent_score', 'Final Result'] \
                if 'Final Playoff Seed' in aggregated_df.columns else \
                ['Manager', 'year', 'win', 'loss', 'team_points', 'opponent_score', 'Final Result']

            display_df = aggregated_df[display_columns]
            display_df = display_df.rename(columns={
                'Final Playoff Seed': 'Seed',
                'year': 'Year',
                'win': 'W',
                'loss': 'L',
                'team_points': 'PF',
                'opponent_score': 'PA'
            })

            years = sorted(display_df['Year'].unique())
            most_recent_year = years[-1] if years else None

            selected_year = st.selectbox("Select Year", years, index=len(years)-1, key=f"{prefix}_year")
            filtered_df = display_df[display_df['Year'] == selected_year]
            if 'Seed' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('Seed', ascending=True)
            st.dataframe(filtered_df, hide_index=True)
        else:
            st.write("The required column 'win' is not available in the data.")

def display_season_standings(df_dict, prefix="season_standings"):
    df = df_dict.get("Matchup Data")
    if df is not None:
        viewer = SeasonStandingsViewer(df)
        viewer.display(prefix=prefix)
    else:
        st.write("No matchup data available.")