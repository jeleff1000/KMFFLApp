import streamlit as st
import pandas as pd

class SeasonStandingsViewer:
    def __init__(self, df):
        self.df = df

    def display(self, prefix=""):
        st.header("Schedules")
        df = self.df

        if 'win' in df.columns:
            df['win'] = df['win'] == 1
            df['loss'] = ~df['win']

            aggregation_type = st.toggle("Per Game", value=False, key=f"{prefix}_aggregation_type")
            aggregation_func = 'mean' if aggregation_type else 'sum'

            aggregated_df = df.groupby(['Manager', 'year']).agg({
                'team_points': aggregation_func,
                'opponent_score': aggregation_func,
                'win': aggregation_func,
                'loss': aggregation_func,
                'is_playoffs': aggregation_func,
                'quarterfinal': aggregation_func,
                'semifinal': aggregation_func,
                'championship': aggregation_func,
                'Champion': aggregation_func
            }).reset_index()

            aggregated_df['year'] = aggregated_df['year'].astype(str)
            managers = sorted(aggregated_df['Manager'].unique())
            col1, col2 = st.columns(2)
            with col1:
                selected_manager = st.selectbox("Select Manager", managers, index=0, key=f"{prefix}_manager")
            with col2:
                years_for_manager = sorted(aggregated_df[aggregated_df['Manager'] == selected_manager]['year'].unique())
                selected_year = st.selectbox("Select Year", years_for_manager, index=len(years_for_manager)-1, key=f"{prefix}_year")

            st.subheader(f"Schedule for {selected_manager} ({selected_year})")

            week_df = df[
                (df['year'].astype(str) == str(selected_year)) & (df['Manager'] == selected_manager)
            ].copy()

            def make_table(filtered_df, title):
                filtered_df['Win'] = filtered_df['win'].apply(lambda x: '✔️' if x else '')
                filtered_df['Loss'] = filtered_df['loss'].apply(lambda x: '✔️' if x else '')
                week_display_cols = [
                    'week', 'Win', 'Loss', 'opponent',
                    'team_points', 'opponent_score', 'team_projected_points', 'opponent_projected_points'
                ]
                week_display_cols = [col for col in week_display_cols if col in filtered_df.columns]
                table = filtered_df[week_display_cols].rename(columns={
                    'team_points': 'PF',
                    'opponent_score': 'PA',
                    'team_projected_points': 'Proj PF',
                    'opponent_projected_points': 'Proj PA'
                })
                # Add totals row
                totals = {}
                for col in ['PF', 'PA', 'Proj PF', 'Proj PA']:
                    if col in table.columns:
                        totals[col] = table[col].sum()
                # Count wins and losses
                if 'Win' in table.columns:
                    totals['Win'] = (table['Win'] == '✔️').sum()
                if 'Loss' in table.columns:
                    totals['Loss'] = (table['Loss'] == '✔️').sum()
                totals_row = {col: "" for col in table.columns}
                totals_row.update(totals)
                totals_row['week'] = "Total"
                table = pd.concat([table, pd.DataFrame([totals_row])], ignore_index=True)
                # Format PF, PA, Proj PF, Proj PA columns to 2 decimals
                format_dict = {col: "{:.2f}" for col in ['PF', 'PA', 'Proj PF', 'Proj PA'] if col in table.columns}
                def big_gray_check(val):
                    if val == '✔️':
                        return 'color: gray; font-size: 2em; text-align: center;'
                    return ''
                st.markdown(f"**{title}**")
                st.dataframe(
                    table.style
                        .applymap(big_gray_check, subset=['Win', 'Loss'])
                        .format(format_dict),
                    hide_index=True
                )

            make_table(week_df[(week_df['is_playoffs'] != 1) & (week_df['is_consolation'] != 1)], "Regular Season")
            make_table(week_df[week_df['is_playoffs'] == 1], "Playoffs")
            make_table(week_df[week_df['is_consolation'] == 1], "Consolation")

        else:
            st.write("The required column 'win' is not available in the data.")

def display_schedules(df_dict, prefix="schedules"):
    df = df_dict.get("Matchup Data")
    if df is not None:
        viewer = SeasonStandingsViewer(df)
        viewer.display(prefix=prefix)
    else:
        st.write("No matchup data available.")