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

        if all(col in merged_data.columns for col in
               ['team_1', 'team_2', 'lineup_position', 'player', 'points', 'fantasy position', 'owner',
                'headshot_url']):
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

            # Hardcoded lineup position order
            position_order = {
                'QB1': 1, 'RB1': 2, 'RB2': 3, 'WR1': 4, 'WR2': 5, 'WR3': 6,
                'TE1': 7, 'W/R/T1': 8, 'K1': 9, 'DEF1': 10
            }

            # Add missing positions with default values
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

            # Sort by hardcoded position order
            display_df['position_order'] = display_df['lineup_position'].map(position_order)
            display_df = display_df.sort_values(by=['position_order']).drop(columns=['position_order']).reset_index(drop=True)

            display_df['margin_1'] = (display_df['points_1'] - display_df['points_2']).round(2)
            display_df['margin_2'] = (display_df['points_2'] - display_df['points_1']).round(2)

            display_df['points_1'] = display_df['points_1'].round(2)
            display_df['points_2'] = display_df['points_2'].round(2)

            # Extract team names
            team_1_name = display_df['team_1'].iloc[0] if not display_df['team_1'].isna().all() else "Team 1"
            team_2_name = display_df['team_2'].iloc[0] if not display_df['team_2'].isna().all() else "Team 2"

            # Filter for main positions and bench/IR positions
            main_positions = ['QB', 'RB', 'WR', 'TE', 'W/R/T', 'K', 'DEF']
            bench_ir_positions = ['BN', 'IR']

            main_df = display_df[display_df['fantasy position'].isin(main_positions)].reset_index(drop=True)
            bench_ir_df = display_df[display_df['fantasy position'].isin(bench_ir_positions)].reset_index(drop=True)

            # Calculate totals for the main positions table
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

            # Render the main positions table
            self.render_table(main_df, team_1_name, team_2_name, color_coding=True)

            # Render the bench and IR table
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

        # Start building the table HTML
        table_html = f"<table><thead><tr>"
        table_html += f"<th colspan='2' style='text-align: center; font-weight: bold; font-size: 16px;'>{team_1_name}</th>"
        table_html += f"<th style='text-align: center; font-weight: bold; font-size: 16px;'>vs</th>"
        table_html += f"<th colspan='2' style='text-align: center; font-weight: bold; font-size: 16px;'>{team_2_name}</th>"
        table_html += "</tr></thead><tbody>"

        if color_coding:
            # Calculate unified margin scale
            global_margin_min = min(df['margin_1'].min(), df['margin_2'].min())
            global_margin_max = max(df['margin_1'].max(), df['margin_2'].max())

        for _, row in df.iterrows():
            if color_coding and row['player_1'] != 'Total':
                # Calculate color scales for unified margin
                margin_1_color = f"rgb({255 - int(200 * (row['margin_1'] - global_margin_min) / (global_margin_max - global_margin_min))}, {int(200 * (row['margin_1'] - global_margin_min) / (global_margin_max - global_margin_min)) + 55}, 55)"
                margin_2_color = f"rgb({255 - int(200 * (row['margin_2'] - global_margin_min) / (global_margin_max - global_margin_min))}, {int(200 * (row['margin_2'] - global_margin_min) / (global_margin_max - global_margin_min)) + 55}, 55)"
                points_1_color = margin_1_color
                points_2_color = margin_2_color
            else:
                points_1_color = "white"
                points_2_color = "white"

            table_html += "<tr>"
            table_html += f"<td><img src='{row['headshot_url_1']}' width='50'><br>{row['player_1']}</td>"
            table_html += f"<td style='background-color: {points_1_color}; font-weight: bold; color: black;'>{row['points_1']}</td>"
            table_html += f"<td>{row['fantasy position']}</td>"
            table_html += f"<td style='background-color: {points_2_color}; font-weight: bold; color: black;'>{row['points_2']}</td>"
            table_html += f"<td><img src='{row['headshot_url_2']}' width='50'><br>{row['player_2']}</td>"
            table_html += "</tr>"

        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)