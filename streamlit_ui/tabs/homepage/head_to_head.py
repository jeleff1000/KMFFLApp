import streamlit as st
import pandas as pd

class H2HViewer:
    def __init__(self, filtered_data, matchup_data):
        self.filtered_data = filtered_data
        self.matchup_data = matchup_data

    def get_matchup_names(self):
        if 'matchup_name' in self.filtered_data.columns:
            return self.filtered_data[['matchup_name']].drop_duplicates()
        else:
            raise KeyError("The required column 'matchup_name' is missing in filtered_data.")

    def display(self, prefix):
        self.filtered_data['season'] = self.filtered_data['season'].fillna(0).astype(int)
        self.matchup_data['year'] = self.matchup_data['year'].fillna(0).astype(int)

        merged_data = pd.merge(
            self.filtered_data,
            self.matchup_data,
            left_on=['owner', 'week', 'season', 'opponent'],
            right_on=['Manager', 'week', 'year', 'opponent'],
            how='inner'
        )

        required_cols = [
            'team_1', 'team_2', 'lineup_position', 'player', 'points',
            'fantasy position', 'owner', 'headshot_url'
        ]
        if all(col in merged_data.columns for col in required_cols):
            default_image_url = "https://static.www.nfl.com/image/private/f_auto,q_auto/league/mdrlzgankwwjldxllgcx"

            team_1_data = merged_data[merged_data['owner'] == merged_data['team_1']][
                ['team_1', 'lineup_position', 'player', 'points', 'fantasy position', 'headshot_url']
            ].rename(columns={'player': 'player_1', 'points': 'points_1', 'headshot_url': 'headshot_url_1'})

            team_2_data = merged_data[merged_data['owner'] == merged_data['team_2']][
                ['team_2', 'lineup_position', 'player', 'points', 'headshot_url']
            ].rename(columns={'player': 'player_2', 'points': 'points_2', 'headshot_url': 'headshot_url_2'})

            team_1_data['headshot_url_1'] = team_1_data['headshot_url_1'].fillna(default_image_url)
            team_2_data['headshot_url_2'] = team_2_data['headshot_url_2'].fillna(default_image_url)

            display_df = pd.merge(
                team_1_data,
                team_2_data,
                on='lineup_position',
                how='outer'
            )

            position_order = {
                'QB1': 1, 'RB1': 2, 'RB2': 3, 'WR1': 4, 'WR2': 5, 'WR3': 6,
                'TE1': 7, 'W/R/T1': 8, 'K1': 9, 'DEF1': 10
            }

            for position in position_order.keys():
                if position not in display_df['lineup_position'].values:
                    display_df = pd.concat([display_df, pd.DataFrame([{
                        'lineup_position': position,
                        'team_1': 'N/A',
                        'player_1': 'N/A',
                        'points_1': 0,
                        'fantasy position': 'N/A',
                        'headshot_url_1': default_image_url,
                        'team_2': 'N/A',
                        'player_2': 'N/A',
                        'points_2': 0,
                        'headshot_url_2': default_image_url
                    }])], ignore_index=True)

            display_df['position_order'] = display_df['lineup_position'].map(position_order)
            display_df = display_df.sort_values(by=['position_order']).drop(columns=['position_order']).reset_index(drop=True)

            display_df['margin_1'] = (display_df['points_1'] - display_df['points_2']).round(2)
            display_df['margin_2'] = (display_df['points_2'] - display_df['points_1']).round(2)

            display_df['points_1'] = display_df['points_1'].round(2)
            display_df['points_2'] = display_df['points_2'].round(2)

            team_1_name = display_df['team_1'].iloc[0] if not display_df['team_1'].isna().all() else "Team 1"
            team_2_name = display_df['team_2'].iloc[0] if not display_df['team_2'].isna().all() else "Team 2"

            main_positions = ['QB', 'RB', 'WR', 'TE', 'W/R/T', 'K', 'DEF']
            bench_ir_positions = ['BN', 'IR']

            main_df = display_df[display_df['fantasy position'].isin(main_positions)].reset_index(drop=True)
            bench_ir_df = display_df[display_df['fantasy position'].isin(bench_ir_positions)].reset_index(drop=True)

            total_points_1 = main_df['points_1'].sum()
            total_points_2 = main_df['points_2'].sum()
            total_row = {
                'player_1': 'Total',
                'points_1': round(total_points_1, 2),
                'fantasy position': '',
                'points_2': round(total_points_2, 2),
                'player_2': '',
                'headshot_url_1': '',
                'headshot_url_2': ''
            }
            main_df = pd.concat([main_df, pd.DataFrame([total_row])], ignore_index=True)

            self.render_table(main_df, team_1_name, team_2_name, color_coding=True)
            self.render_table(bench_ir_df, team_1_name, team_2_name, color_coding=False)
        else:
            st.write("The required columns are not available in the data.")

    def render_table(self, df, team_1_name, team_2_name, color_coding):
        st.markdown(
            f"""
            <style>
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        table_html = f"<table><thead><tr>"
        table_html += f"<th colspan='2' style='text-align: center; font-weight: bold; font-size: 16px;'>{team_1_name}</th>"
        table_html += f"<th style='text-align: center; font-weight: bold; font-size: 16px;'>vs</th>"
        table_html += f"<th colspan='2' style='text-align: center; font-weight: bold; font-size: 16px;'>{team_2_name}</th>"
        table_html += "</tr></thead><tbody>"

        if color_coding and 'margin_1' in df.columns and 'margin_2' in df.columns:
            global_margin_min = min(df['margin_1'].min(), df['margin_2'].min())
            global_margin_max = max(df['margin_1'].max(), df['margin_2'].max())

        for _, row in df.iterrows():
            if color_coding and row.get('player_1', '') != 'Total' and 'margin_1' in row and 'margin_2' in row:
                margin_1_color = f"rgb({255 - int(200 * (row['margin_1'] - global_margin_min) / (global_margin_max - global_margin_min))}, {int(200 * (row['margin_1'] - global_margin_min) / (global_margin_max - global_margin_min)) + 55}, 55)"
                margin_2_color = f"rgb({255 - int(200 * (row['margin_2'] - global_margin_min) / (global_margin_max - global_margin_min))}, {int(200 * (row['margin_2'] - global_margin_min) / (global_margin_max - global_margin_min)) + 55}, 55)"
                points_1_color = margin_1_color
                points_2_color = margin_2_color
            else:
                points_1_color = "white"
                points_2_color = "white"

            table_html += "<tr>"
            table_html += f"<td><img src='{row.get('headshot_url_1', '')}' width='50'><br>{row.get('player_1', '')}</td>"
            table_html += f"<td style='background-color: {points_1_color}; font-weight: bold; color: black;'>{row.get('points_1', '')}</td>"
            table_html += f"<td>{row.get('fantasy position', '')}</td>"
            table_html += f"<td style='background-color: {points_2_color}; font-weight: bold; color: black;'>{row.get('points_2', '')}</td>"
            table_html += f"<td><img src='{row.get('headshot_url_2', '')}' width='50'><br>{row.get('player_2', '')}</td>"
            table_html += "</tr>"

        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

def filter_h2h_data(player_data, year, week, matchup_name):
    df = player_data.copy()
    if year is not None:
        df = df[df['season'] == int(year)]
    if week is not None:
        df = df[df['week'] == int(week)]
    if matchup_name is not None:
        df = df[df['matchup_name'] == matchup_name]
    return df

def display_head_to_head(df_dict):
    player_data = df_dict.get("Player Data")
    matchup_data = df_dict.get("Matchup Data")
    if player_data is None or matchup_data is None:
        st.write("Player Data or Matchup Data not found.")
        return

    key_prefix = "h2h_head_to_head_"

    # Normalize numeric fields
    player_data = player_data.copy()
    matchup_data = matchup_data.copy()
    player_data['season'] = pd.to_numeric(player_data['season'], errors='coerce')
    player_data['week'] = pd.to_numeric(player_data['week'], errors='coerce')
    matchup_data['year'] = pd.to_numeric(matchup_data['year'], errors='coerce')
    matchup_data['week'] = pd.to_numeric(matchup_data['week'], errors='coerce')

    # Intersect available (season/year, week) combos that exist in BOTH datasets
    pd_pairs = player_data[['season', 'week']].dropna().drop_duplicates()
    md_pairs = matchup_data.rename(columns={'year': 'season'})[['season', 'week']].dropna().drop_duplicates()
    avail_pairs = (
        pd.merge(pd_pairs, md_pairs, on=['season', 'week'], how='inner')
        .drop_duplicates()
        .sort_values(['season', 'week'])
    )

    if avail_pairs.empty:
        st.write("No overlapping year/week combinations in Player Data and Matchup Data.")
        return

    years = sorted(avail_pairs['season'].astype(int).unique())
    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])

    with col1:
        selected_year = st.selectbox(
            "Select Year",
            years,
            index=len(years) - 1,  # default to largest year with data in both
            key=f"{key_prefix}year_value",
        )

    with col2:
        weeks = sorted(
            avail_pairs.loc[avail_pairs['season'] == selected_year, 'week'].astype(int).unique()
        )
        if weeks:
            selected_week = st.selectbox(
                "Select Week",
                weeks,
                index=len(weeks) - 1,  # default to largest available week for selected year
                key=f"{key_prefix}week_value",
            )
        else:
            selected_week = None
            st.selectbox(
                "Select Week",
                options=[],
                key=f"{key_prefix}week_value",
                disabled=True,
                placeholder="No weeks",
            )

    with col3:
        if selected_year and selected_week is not None:
            matchups = player_data[
                (player_data['season'] == selected_year) & (player_data['week'] == selected_week)
            ]['matchup_name'].dropna().astype(str).unique()
            matchups = sorted(matchups)
            selected_matchup_name = (
                st.selectbox(
                    "Select Matchup Name",
                    matchups,
                    index=0 if matchups else None,
                    key=f"{key_prefix}matchup_name_value",
                )
                if matchups else None
            )
        else:
            selected_matchup_name = None
            st.selectbox(
                "Select Matchup Name",
                options=[],
                key=f"{key_prefix}matchup_name_value",
                disabled=True,
                placeholder="No matchups",
            )

    with col4:
        go_button = st.button("Go", key=f"{key_prefix}go_button")

    if go_button and selected_year and (selected_week is not None) and selected_matchup_name:
        filtered_h2h = filter_h2h_data(player_data, selected_year, selected_week, selected_matchup_name)
        viewer = H2HViewer(filtered_h2h, matchup_data)
        viewer.display(prefix="h2h")
    elif not go_button:
        st.write("Please select a year, week, and matchup name, then click 'Go' to view H2H data.")