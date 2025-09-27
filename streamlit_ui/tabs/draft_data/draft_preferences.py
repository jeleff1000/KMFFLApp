import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def order_positions(df, position_col='position', allowed_positions=None):
    if allowed_positions is None:
        allowed_positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
    position_order = pd.CategoricalDtype(allowed_positions, ordered=True)
    df = df[df[position_col].isin(allowed_positions)].copy()
    df[position_col] = df[position_col].astype(position_order)
    return df.sort_values([position_col])

def display_draft_preferences(draft_data, player_df):
    st.header("Draft Preferences")

    # Standardize column names to snake_case
    draft_data = draft_data.rename(columns={
        'Year': 'year',
        'Team Manager': 'manager',
        'Primary Position': 'primary_position',
        'Name Full': 'player_name',
        'Cost': 'cost',
        'Is Keeper Status': 'is_keeper_status',
        'Pick': 'pick'
    })
    player_df = player_df.rename(columns={
        'position': 'position',  # already snake_case
        'year': 'year',
        'player': 'player',
        'points': 'points',
        'week': 'week',
        'playeryear': 'playeryear'
    })

    draft_data['year'] = draft_data['year'].astype(str)
    draft_data['manager'] = draft_data['manager'].astype(str)
    player_df['year'] = player_df['year'].astype(str)

    if 'position' not in player_df.columns:
        st.error("The 'position' column is missing from player_df.")
        return

    allowed_primary_positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    # Remove years where all costs are zero
    nonzero_years = draft_data.groupby('year')['cost'].sum()
    valid_years = nonzero_years[nonzero_years != 0].index.tolist()
    draft_data = draft_data[draft_data['year'].isin(valid_years)]
    draft_data = draft_data[draft_data['manager'].notna()]
    draft_data = draft_data[draft_data['manager'].str.lower() != 'nan']

    years = sorted(draft_data['year'].unique().tolist())
    team_managers = ['League Average'] + sorted(draft_data['manager'].unique().tolist()) + ['League Total']

    tabs = st.tabs(["Draft Tables", "Cost Over Time Graph"])

    with tabs[0]:
        col1, col2, col3 = st.columns(3)
        with col1:
            start_year = st.selectbox("Start Year", years, index=0)
        with col2:
            end_year = st.selectbox("End Year", years, index=len(years)-1)
        with col3:
            selected_manager = st.selectbox("Select Manager", team_managers, index=0)

        selected_years = [y for y in years if start_year <= y <= end_year]

        if selected_manager == 'League Total':
            st.subheader("League Total Draft Data")
            columns_to_show = ['year', 'manager', 'cost', 'primary_position', 'is_keeper_status']

            filtered = draft_data[
                draft_data['is_keeper_status'].ne(1).fillna(True) &
                (draft_data['manager'].str.strip() != '')
            ].copy()

            if 'primary_position' in filtered.columns and 'cost' in filtered.columns:
                filtered['RankNum'] = filtered.groupby(['year', 'primary_position'])['cost'] \
                    .rank(method='first', ascending=False).astype(int)
                filtered['personal_position_rank'] = filtered['primary_position'] + filtered['RankNum'].astype(str)
                columns_to_show.append('personal_position_rank')

            columns_to_show = [col for col in columns_to_show if col in filtered.columns]
            st.dataframe(filtered[columns_to_show], hide_index=True)
        else:
            def get_drafted_table(filtered_draft_data, table_title):
                if selected_years:
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['year'].isin(selected_years)]
                    player_df_filtered = player_df[player_df['year'].isin(selected_years)]
                else:
                    player_df_filtered = player_df

                if selected_manager and selected_manager != 'League Average':
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['manager'] == selected_manager]

                right_cols = [c for c in ['playeryear', 'player', 'points', 'week', 'year', 'position']
                              if c in player_df_filtered.columns]

                merged_data = filtered_draft_data.merge(
                    player_df_filtered[right_cols],
                    left_on=['player_name', 'year'],
                    right_on=['player', 'year'],
                    how='left'
                )

                merged_data = merged_data[
                    ((merged_data['year'].astype(int) < 2021) & (merged_data['week'] <= 16)) |
                    ((merged_data['year'].astype(int) >= 2021) & (merged_data['week'] <= 17))
                ]

                aggregated_data = merged_data.groupby(['year', 'player', 'position']).agg({
                    'points': 'sum',
                    'cost': 'first',
                    'pick': 'first',
                    'player_name': 'first',
                    'manager': 'first',
                    'week': pd.Series.nunique
                }).reset_index()

                aggregated_data['ppg'] = (aggregated_data['points'] / aggregated_data['week']).round(2)
                aggregated_data['personal_position_rank'] = (
                    aggregated_data.groupby(['year', 'position', 'manager'])['cost']
                    .rank(method='first', ascending=False)
                    .astype(int)
                    .astype(str)
                )
                aggregated_data['personal_position_rank'] = aggregated_data['position'] + aggregated_data['personal_position_rank']

                aggregated_data = order_positions(aggregated_data, position_col='position', allowed_positions=allowed_primary_positions)
                aggregated_data = aggregated_data[aggregated_data['cost'] > 0]

                # Remove years where all costs are zero in the aggregated data
                nonzero_years_agg = aggregated_data.groupby('year')['cost'].sum()
                valid_years_agg = nonzero_years_agg[nonzero_years_agg != 0].index.tolist()
                aggregated_data = aggregated_data[aggregated_data['year'].isin(valid_years_agg)]

                if selected_manager == 'League Average':
                    avg_data = aggregated_data.groupby(
                        ['personal_position_rank', 'position']
                    ).agg(
                        avg_cost=('cost', 'mean'),
                        max_cost=('cost', 'max'),
                        min_cost=('cost', 'min'),
                        median_cost=('cost', 'median'),
                        ppg=('ppg', 'mean'),
                        times_drafted=('personal_position_rank', 'count')
                    ).reset_index()
                    avg_data['manager'] = 'League Average'
                else:
                    avg_data = aggregated_data.groupby(
                        ['personal_position_rank', 'position', 'manager']
                    ).agg(
                        avg_cost=('cost', 'mean'),
                        max_cost=('cost', 'max'),
                        min_cost=('cost', 'min'),
                        median_cost=('cost', 'median'),
                        ppg=('ppg', 'mean'),
                        times_drafted=('personal_position_rank', 'count')
                    ).reset_index()

                for col in ['avg_cost', 'max_cost', 'min_cost', 'median_cost', 'ppg']:
                    avg_data[col] = avg_data[col].round(2)

                score_cols = ['avg_cost', 'ppg', 'times_drafted']
                avg_data = avg_data[~((avg_data[score_cols].isnull()) | (avg_data[score_cols] == 0)).all(axis=1)]

                avg_data['rank_num'] = avg_data['personal_position_rank'].str.extract(r'(\d+)$').fillna(0).astype(int)
                avg_data = order_positions(avg_data, position_col='position', allowed_positions=allowed_primary_positions)
                avg_data = avg_data.sort_values(['position', 'rank_num'])

                columns_to_display = [
                    'personal_position_rank', 'position', 'manager',
                    'avg_cost', 'max_cost', 'min_cost', 'median_cost', 'ppg', 'times_drafted'
                ]
                st.subheader(table_title)
                st.dataframe(avg_data[columns_to_display], hide_index=True)

            def get_kept_table(filtered_draft_data, table_title):
                if selected_years:
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['year'].isin(selected_years)]
                    player_df_filtered = player_df[player_df['year'].isin(selected_years)]
                else:
                    player_df_filtered = player_df

                if selected_manager and selected_manager != 'League Average':
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['manager'] == selected_manager]

                right_cols = [c for c in ['playeryear', 'player', 'points', 'week', 'year', 'position']
                              if c in player_df_filtered.columns]

                merged_data = filtered_draft_data.merge(
                    player_df_filtered[right_cols],
                    left_on=['player_name', 'year'],
                    right_on=['player', 'year'],
                    how='left'
                )

                merged_data = merged_data[
                    ((merged_data['year'].astype(int) < 2021) & (merged_data['week'] <= 16)) |
                    ((merged_data['year'].astype(int) >= 2021) & (merged_data['week'] <= 17))
                ]

                player_data = merged_data.groupby(['player', 'position', 'manager']).agg({
                    'cost': 'first',
                    'points': 'sum',
                    'week': pd.Series.nunique
                }).reset_index()
                player_data['ppg'] = (player_data['points'] / player_data['week']).round(2)

                player_data = order_positions(player_data, position_col='position', allowed_positions=allowed_primary_positions)
                player_data = player_data[player_data['cost'] > 0]

                # Remove years where all costs are zero in the player data
                nonzero_years_player = player_data.groupby('player')['cost'].sum()
                valid_players = nonzero_years_player[nonzero_years_player != 0].index.tolist()
                player_data = player_data[player_data['player'].isin(valid_players)]

                if selected_manager == 'League Average':
                    avg_data = player_data.groupby(['position']).agg(
                        avg_cost=('cost', 'mean'),
                        max_cost=('cost', 'max'),
                        min_cost=('cost', 'min'),
                        median_cost=('cost', 'median'),
                        ppg=('ppg', 'mean'),
                        times_kept=('player', 'count')
                    ).reset_index()
                    avg_data['manager'] = 'League Average'
                else:
                    avg_data = player_data.groupby(['position', 'manager']).agg(
                        avg_cost=('cost', 'mean'),
                        max_cost=('cost', 'max'),
                        min_cost=('cost', 'min'),
                        median_cost=('cost', 'median'),
                        ppg=('ppg', 'mean'),
                        times_kept=('player', 'count')
                    ).reset_index()

                for col in ['avg_cost', 'max_cost', 'min_cost', 'median_cost', 'ppg']:
                    avg_data[col] = avg_data[col].round(2)

                score_cols = ['avg_cost', 'ppg', 'times_kept']
                avg_data = avg_data[~((avg_data[score_cols].isnull()) | (avg_data[score_cols] == 0)).all(axis=1)]

                avg_data = order_positions(avg_data, position_col='position', allowed_positions=allowed_primary_positions)
                avg_data = avg_data.sort_values(['position'])

                columns_to_display = [
                    'position', 'manager',
                    'avg_cost', 'max_cost', 'min_cost', 'median_cost', 'ppg', 'times_kept'
                ]
                st.subheader(table_title)
                st.dataframe(avg_data[columns_to_display], hide_index=True)

            get_drafted_table(draft_data[draft_data['is_keeper_status'].ne(1).fillna(True)], "Drafted Players")
            get_kept_table(draft_data[draft_data['is_keeper_status'].eq(1).fillna(False)], "Kept Players")

    # The rest of the code for the graph tab would be similarly updated to use snake_case columns.
    # For brevity, only the table logic is shown here, but apply the same renaming to the graph logic.