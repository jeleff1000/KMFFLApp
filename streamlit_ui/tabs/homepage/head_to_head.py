import duckdb
import pandas as pd
import streamlit as st

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
        # Normalize types
        self.filtered_data['year'] = pd.to_numeric(self.filtered_data['year'], errors='coerce').fillna(0).astype(int)
        self.matchup_data['year']  = pd.to_numeric(self.matchup_data['year'],  errors='coerce').fillna(0).astype(int)

        self.filtered_data['week'] = pd.to_numeric(self.filtered_data['week'], errors='coerce')
        self.matchup_data['week']  = pd.to_numeric(self.matchup_data['week'],  errors='coerce')

        # Optional: unify team_name if matchup_data has 'team' instead
        mcols = {c.lower(): c for c in self.matchup_data.columns}
        if 'team_name' not in mcols and 'team' in mcols:
            self.matchup_data = self.matchup_data.rename(columns={mcols['team']: 'team_name'})

        # DuckDB connection
        con = duckdb.connect()
        con.register('filtered', self.filtered_data)
        con.register('matchup', self.matchup_data)

        # Join on keys, but take team_1 / team_2 from filtered (source of truth here)
        merged_data = con.execute("""
            SELECT
                f.*,
                f.team_1 AS team_1,
                f.team_2 AS team_2
            FROM filtered f
            INNER JOIN matchup m
              ON f.manager  = m.manager
             AND f.opponent = m.opponent
             AND f.week     = m.week
             AND f.year     = m.year
        """).df()

        required_cols = [
            'team_1', 'team_2', 'player', 'points',
            'fantasy_position', 'manager', 'headshot_url'
        ]
        if all(col in merged_data.columns for col in required_cols):
            default_image_url = "https://static.www.nfl.com/image/private/f_auto,q_auto/league/mdrlzgankwwjldxllgcx"

            team_1 = merged_data['team_1'].iloc[0]
            team_2 = merged_data['team_2'].iloc[0]

            position_order = ['QB', 'RB', 'WR', 'TE', 'W/R/T', 'K', 'DEF']
            bench_ir_positions = ['BN', 'IR']

            def prepare_team_duckdb(df, manager, team_col, player_col, points_col, fantasy_pos_col, headshot_col, positions):
                con.register('team_df', df)
                pos_order_map = {pos: i for i, pos in enumerate(positions)}
                pos_order_case = "CASE " + " ".join([f"WHEN {fantasy_pos_col}='{pos}' THEN {i}" for pos, i in pos_order_map.items()]) + " ELSE 999 END"
                query = f"""
                    SELECT
                        {team_col},
                        {fantasy_pos_col},
                        {player_col},
                        {points_col},
                        COALESCE(NULLIF({headshot_col}, ''), '{default_image_url}') AS {headshot_col},
                        ROW_NUMBER() OVER (PARTITION BY {fantasy_pos_col} ORDER BY {points_col} DESC) - 1 AS slot
                    FROM team_df
                    WHERE manager = '{manager}'
                      AND {fantasy_pos_col} IN ({','.join([f"'{p}'" for p in positions])})
                    ORDER BY {pos_order_case}, {points_col} DESC
                """
                return con.execute(query).df()

            # Main positions
            team_1_main = prepare_team_duckdb(
                merged_data, team_1, 'team_1', 'player', 'points', 'fantasy_position', 'headshot_url', position_order
            ).rename(columns={'player': 'player_1', 'points': 'points_1', 'headshot_url': 'headshot_url_1'})
            team_2_main = prepare_team_duckdb(
                merged_data, team_2, 'team_2', 'player', 'points', 'fantasy_position', 'headshot_url', position_order
            ).rename(columns={'player': 'player_2', 'points': 'points_2', 'headshot_url': 'headshot_url_2'})

            con.register('team_1_main', team_1_main)
            con.register('team_2_main', team_2_main)
            main_df = con.execute("""
                SELECT
                    t1.*,
                    t2.player_2, t2.points_2, t2.headshot_url_2, t2.team_2
                FROM team_1_main t1
                FULL OUTER JOIN team_2_main t2
                  ON t1.fantasy_position = t2.fantasy_position
                 AND t1.slot = t2.slot
            """).df()

            main_df['points_1'] = main_df['points_1'].fillna(0).round(2)
            main_df['points_2'] = main_df['points_2'].fillna(0).round(2)
            main_df['margin_1'] = (main_df['points_1'] - main_df['points_2']).round(2)
            main_df['margin_2'] = (main_df['points_2'] - main_df['points_1']).round(2)

            team_1_name = main_df['team_1'].iloc[0] if not main_df['team_1'].isna().all() else "Team 1"
            team_2_name = main_df['team_2'].iloc[0] if not main_df['team_2'].isna().all() else "Team 2"

            main_df['position_order'] = main_df['fantasy_position'].map({pos: i for i, pos in enumerate(position_order)})
            main_df = main_df.sort_values(['position_order', 'slot']).drop(columns=['position_order']).reset_index(drop=True)

            total_points_1 = main_df['points_1'].sum()
            total_points_2 = main_df['points_2'].sum()
            total_row = {
                'player_1': 'Total',
                'points_1': round(total_points_1, 2),
                'fantasy_position': '',
                'points_2': round(total_points_2, 2),
                'player_2': '',
                'headshot_url_1': '',
                'headshot_url_2': ''
            }
            main_df = pd.concat([main_df, pd.DataFrame([total_row])], ignore_index=True)

            # Bench/IR positions
            team_1_bench = prepare_team_duckdb(
                merged_data, team_1, 'team_1', 'player', 'points', 'fantasy_position', 'headshot_url', bench_ir_positions
            ).rename(columns={'player': 'player_1', 'points': 'points_1', 'headshot_url': 'headshot_url_1'})
            team_2_bench = prepare_team_duckdb(
                merged_data, team_2, 'team_2', 'player', 'points', 'fantasy_position', 'headshot_url', bench_ir_positions
            ).rename(columns={'player': 'player_2', 'points': 'points_2', 'headshot_url': 'headshot_url_2'})

            con.register('team_1_bench', team_1_bench)
            con.register('team_2_bench', team_2_bench)
            bench_ir_df = con.execute("""
                SELECT
                    t1.*,
                    t2.player_2, t2.points_2, t2.headshot_url_2, t2.team_2
                FROM team_1_bench t1
                FULL OUTER JOIN team_2_bench t2
                  ON t1.fantasy_position = t2.fantasy_position
                 AND t1.slot = t2.slot
            """).df()

            bench_ir_df['points_1'] = bench_ir_df['points_1'].fillna(0).round(2)
            bench_ir_df['points_2'] = bench_ir_df['points_2'].fillna(0).round(2)
            bench_ir_df['margin_1'] = (bench_ir_df['points_1'] - bench_ir_df['points_2']).round(2)
            bench_ir_df['margin_2'] = (bench_ir_df['points_2'] - bench_ir_df['points_1']).round(2)
            bench_ir_df = bench_ir_df.sort_values(['fantasy_position', 'slot']).reset_index(drop=True)

            self.render_table(main_df, team_1_name, team_2_name, color_coding=True)
            self.render_table(bench_ir_df, team_1_name, team_2_name, color_coding=False)
        else:
            missing = [c for c in required_cols if c not in merged_data.columns]
            st.write(f"The required columns are not available in the data. Missing: {missing}")

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
            margin_1_min = df['margin_1'].min(skipna=True)
            margin_2_min = df['margin_2'].min(skipna=True)
            margin_1_max = df['margin_1'].max(skipna=True)
            margin_2_max = df['margin_2'].max(skipna=True)
            global_margin_min = min(margin_1_min if pd.notna(margin_1_min) else 0,
                                    margin_2_min if pd.notna(margin_2_min) else 0)
            global_margin_max = max(margin_1_max if pd.notna(margin_1_max) else 0,
                                    margin_2_max if pd.notna(margin_2_max) else 0)
            margin_range = global_margin_max - global_margin_min
            if margin_range == 0:
                margin_range = 1

        for _, row in df.iterrows():
            if color_coding and row.get('player_1', '') != 'Total' and 'margin_1' in row and 'margin_2' in row:
                m1 = row['margin_1'] if pd.notna(row['margin_1']) else 0
                m2 = row['margin_2'] if pd.notna(row['margin_2']) else 0
                margin_1_color = f"rgb({255 - int(200 * (m1 - global_margin_min) / margin_range)}, {int(200 * (m1 - global_margin_min) / margin_range) + 55}, 55)"
                margin_2_color = f"rgb({255 - int(200 * (m2 - global_margin_min) / margin_range)}, {int(200 * (m2 - global_margin_min) / margin_range) + 55}, 55)"
                points_1_color = margin_1_color
                points_2_color = margin_2_color
            else:
                points_1_color = "white"
                points_2_color = "white"

            table_html += "<tr>"
            table_html += f"<td><img src='{row.get('headshot_url_1', '')}' width='50'><br>{row.get('player_1', '')}</td>"
            table_html += f"<td style='background-color: {points_1_color}; font-weight: bold; color: black;'>{row.get('points_1', '')}</td>"
            table_html += f"<td>{row.get('fantasy_position', '')}</td>"
            table_html += f"<td style='background-color: {points_2_color}; font-weight: bold; color: black;'>{row.get('points_2', '')}</td>"
            table_html += f"<td><img src='{row.get('headshot_url_2', '')}' width='50'><br>{row.get('player_2', '')}</td>"
            table_html += "</tr>"

        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)


def filter_h2h_data(player_data, year, week, matchup_name):
    con = duckdb.connect()
    con.register('player_data', player_data)
    query = f"""
        SELECT *
        FROM player_data
        WHERE year = {int(year)}
          AND week = {int(week)}
          AND matchup_name = '{matchup_name.replace("'", "''")}'
    """
    return con.execute(query).df()


def display_head_to_head(df_dict):
    player_data = df_dict.get("Player Data")
    matchup_data = df_dict.get("Matchup Data")
    if player_data is None or matchup_data is None:
        st.write("Player Data or Matchup Data not found.")
        return

    key_prefix = "h2h_head_to_head_"

    player_data = player_data.copy()
    matchup_data = matchup_data.copy()
    player_data['year'] = pd.to_numeric(player_data['year'], errors='coerce')
    player_data['week'] = pd.to_numeric(player_data['week'], errors='coerce')
    matchup_data['year'] = pd.to_numeric(matchup_data['year'], errors='coerce')
    matchup_data['week'] = pd.to_numeric(matchup_data['week'], errors='coerce')

    con = duckdb.connect()
    con.register('player_data', player_data)
    con.register('matchup_data', matchup_data)
    pd_pairs = con.execute("""
        SELECT DISTINCT year, week
        FROM player_data
        WHERE year IS NOT NULL AND week IS NOT NULL
    """).df()
    md_pairs = con.execute("""
        SELECT DISTINCT year, week
        FROM matchup_data
        WHERE year IS NOT NULL AND week IS NOT NULL
    """).df()
    avail_pairs = pd.merge(pd_pairs, md_pairs, on=['year', 'week'], how='inner') \
                    .drop_duplicates().sort_values(['year', 'week'])

    if avail_pairs.empty:
        st.write("No overlapping year/week combinations in Player Data and Matchup Data.")
        return

    years = sorted(avail_pairs['year'].astype(int).unique())
    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])

    with col1:
        selected_year = st.selectbox(
            "Select Year",
            years,
            index=len(years) - 1,
            key=f"{key_prefix}year_value",
        )

    with col2:
        weeks = sorted(
            avail_pairs.loc[avail_pairs['year'] == selected_year, 'week'].astype(int).unique()
        )
        if weeks:
            selected_week = st.selectbox(
                "Select Week",
                weeks,
                index=len(weeks) - 1,
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
                (player_data['year'] == selected_year) & (player_data['week'] == selected_week)
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
