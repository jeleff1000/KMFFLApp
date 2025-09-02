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

    draft_data['Year'] = draft_data['Year'].astype(str)
    draft_data['Team Manager'] = draft_data['Team Manager'].astype(str)
    player_df['season'] = player_df['season'].astype(str)

    if 'position' not in player_df.columns:
        st.error("The 'position' column is missing from player_df.")
        return

    allowed_primary_positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    # Remove years where all costs are zero
    nonzero_years = draft_data.groupby('Year')['Cost'].sum()
    valid_years = nonzero_years[nonzero_years != 0].index.tolist()
    draft_data = draft_data[draft_data['Year'].isin(valid_years)]
    draft_data = draft_data[draft_data['Team Manager'].notna()]
    draft_data = draft_data[draft_data['Team Manager'].str.lower() != 'nan']

    years = sorted(draft_data['Year'].unique().tolist())
    team_managers = ['League Average'] + sorted(draft_data['Team Manager'].unique().tolist()) + ['League Total']

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
            columns_to_show = ['Year', 'Team Manager', 'Cost', 'Primary Position', 'Is Keeper Status']

            filtered = draft_data[
                (draft_data['Is Keeper Status'] != 1) &
                (draft_data['Team Manager'].str.strip() != '')
            ].copy()

            if 'Primary Position' in filtered.columns and 'Cost' in filtered.columns:
                filtered['RankNum'] = filtered.groupby(['Year', 'Primary Position'])['Cost'] \
                    .rank(method='first', ascending=False).astype(int)
                filtered['Personal Position Rank'] = filtered['Primary Position'] + filtered['RankNum'].astype(str)
                columns_to_show.append('Personal Position Rank')

            columns_to_show = [col for col in columns_to_show if col in filtered.columns]
            st.dataframe(filtered[columns_to_show], hide_index=True)
        else:
            def get_drafted_table(filtered_draft_data, table_title):
                if selected_years:
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['Year'].isin(selected_years)]
                    player_df_filtered = player_df[player_df['playeryear'].str.contains('|'.join(selected_years))]
                else:
                    player_df_filtered = player_df

                if selected_manager and selected_manager != 'League Average':
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['Team Manager'] == selected_manager]

                merged_data = filtered_draft_data.merge(
                    player_df_filtered[['playeryear', 'player', 'points', 'week', 'season', 'position']],
                    left_on=['Name Full', 'Year'],
                    right_on=['player', 'season'],
                    how='left'
                )

                merged_data = merged_data[
                    (merged_data['Year'].astype(int) < 2021) & (merged_data['week'] <= 16) |
                    (merged_data['Year'].astype(int) >= 2021) & (merged_data['week'] <= 17)
                ]

                aggregated_data = merged_data.groupby(['season', 'player', 'position']).agg({
                    'points': 'sum',
                    'Cost': 'first',
                    'Pick': 'first',
                    'Name Full': 'first',
                    'Team Manager': 'first',
                    'week': pd.Series.nunique
                }).reset_index()

                aggregated_data['PPG'] = (aggregated_data['points'] / aggregated_data['week']).round(2)
                aggregated_data['Personal Position Rank'] = (
                    aggregated_data.groupby(['season', 'position', 'Team Manager'])['Cost']
                    .rank(method='first', ascending=False)
                    .astype(int)
                    .astype(str)
                )
                aggregated_data['Personal Position Rank'] = aggregated_data['position'] + aggregated_data['Personal Position Rank']

                aggregated_data = order_positions(aggregated_data, position_col='position', allowed_positions=allowed_primary_positions)
                aggregated_data = aggregated_data[aggregated_data['Cost'] > 0]

                # Remove years where all costs are zero in the aggregated data
                nonzero_years_agg = aggregated_data.groupby('season')['Cost'].sum()
                valid_years_agg = nonzero_years_agg[nonzero_years_agg != 0].index.tolist()
                aggregated_data = aggregated_data[aggregated_data['season'].isin(valid_years_agg)]

                if selected_manager == 'League Average':
                    avg_data = aggregated_data.groupby(
                        ['Personal Position Rank', 'position']
                    ).agg(
                        Avg_Cost=('Cost', 'mean'),
                        Max_Cost=('Cost', 'max'),
                        Min_Cost=('Cost', 'min'),
                        Median_Cost=('Cost', 'median'),
                        PPG=('PPG', 'mean'),
                        Times_Drafted=('Personal Position Rank', 'count')
                    ).reset_index()
                    avg_data['Team Manager'] = 'League Average'
                else:
                    avg_data = aggregated_data.groupby(
                        ['Personal Position Rank', 'position', 'Team Manager']
                    ).agg(
                        Avg_Cost=('Cost', 'mean'),
                        Max_Cost=('Cost', 'max'),
                        Min_Cost=('Cost', 'min'),
                        Median_Cost=('Cost', 'median'),
                        PPG=('PPG', 'mean'),
                        Times_Drafted=('Personal Position Rank', 'count')
                    ).reset_index()

                for col in ['Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG']:
                    avg_data[col] = avg_data[col].round(2)

                score_cols = ['Avg_Cost', 'PPG', 'Times_Drafted']
                avg_data = avg_data[~((avg_data[score_cols].isnull()) | (avg_data[score_cols] == 0)).all(axis=1)]

                avg_data['RankNum'] = avg_data['Personal Position Rank'].str.extract(r'(\d+)$').fillna(0).astype(int)
                avg_data = order_positions(avg_data, position_col='position', allowed_positions=allowed_primary_positions)
                avg_data = avg_data.sort_values(['position', 'RankNum'])

                columns_to_display = [
                    'Personal Position Rank', 'position', 'Team Manager',
                    'Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG', 'Times_Drafted'
                ]
                st.subheader(table_title)
                st.dataframe(avg_data[columns_to_display], hide_index=True)

            def get_kept_table(filtered_draft_data, table_title):
                if selected_years:
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['Year'].isin(selected_years)]
                    player_df_filtered = player_df[player_df['playeryear'].str.contains('|'.join(selected_years))]
                else:
                    player_df_filtered = player_df

                if selected_manager and selected_manager != 'League Average':
                    filtered_draft_data = filtered_draft_data[filtered_draft_data['Team Manager'] == selected_manager]

                merged_data = filtered_draft_data.merge(
                    player_df_filtered[['playeryear', 'player', 'points', 'week', 'season', 'position']],
                    left_on=['Name Full', 'Year'],
                    right_on=['player', 'season'],
                    how='left'
                )

                merged_data = merged_data[
                    (merged_data['Year'].astype(int) < 2021) & (merged_data['week'] <= 16) |
                    (merged_data['Year'].astype(int) >= 2021) & (merged_data['week'] <= 17)
                ]

                player_data = merged_data.groupby(['player', 'position', 'Team Manager']).agg({
                    'Cost': 'first',
                    'points': 'sum',
                    'week': pd.Series.nunique
                }).reset_index()
                player_data['PPG'] = (player_data['points'] / player_data['week']).round(2)

                player_data = order_positions(player_data, position_col='position', allowed_positions=allowed_primary_positions)
                player_data = player_data[player_data['Cost'] > 0]

                # Remove years where all costs are zero in the player data
                nonzero_years_player = player_data.groupby('player')['Cost'].sum()
                valid_players = nonzero_years_player[nonzero_years_player != 0].index.tolist()
                player_data = player_data[player_data['player'].isin(valid_players)]

                if selected_manager == 'League Average':
                    avg_data = player_data.groupby(['position']).agg(
                        Avg_Cost=('Cost', 'mean'),
                        Max_Cost=('Cost', 'max'),
                        Min_Cost=('Cost', 'min'),
                        Median_Cost=('Cost', 'median'),
                        PPG=('PPG', 'mean'),
                        Times_Kept=('player', 'count')
                    ).reset_index()
                    avg_data['Team Manager'] = 'League Average'
                else:
                    avg_data = player_data.groupby(['position', 'Team Manager']).agg(
                        Avg_Cost=('Cost', 'mean'),
                        Max_Cost=('Cost', 'max'),
                        Min_Cost=('Cost', 'min'),
                        Median_Cost=('Cost', 'median'),
                        PPG=('PPG', 'mean'),
                        Times_Kept=('player', 'count')
                    ).reset_index()

                for col in ['Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG']:
                    avg_data[col] = avg_data[col].round(2)

                score_cols = ['Avg_Cost', 'PPG', 'Times_Kept']
                avg_data = avg_data[~((avg_data[score_cols].isnull()) | (avg_data[score_cols] == 0)).all(axis=1)]

                avg_data = order_positions(avg_data, position_col='position', allowed_positions=allowed_primary_positions)
                avg_data = avg_data.sort_values(['position'])

                columns_to_display = [
                    'position', 'Team Manager',
                    'Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG', 'Times_Kept'
                ]
                st.subheader(table_title)
                st.dataframe(avg_data[columns_to_display], hide_index=True)

            get_drafted_table(draft_data[draft_data['Is Keeper Status'] != 1], "Drafted Players")
            get_kept_table(draft_data[draft_data['Is Keeper Status'] == 1], "Kept Players")

    with tabs[1]:
        st.subheader("Cost Over Time")
        col1, col2 = st.columns(2)
        # Clean manager list
        team_managers_clean = [m for m in draft_data['Team Manager'].dropna().unique() if m != 'League Total']
        team_managers = ['League Average'] + sorted(team_managers_clean)
        with col1:
            selected_manager_graph = st.selectbox("Manager", team_managers, index=0, key="graph_manager")
        with col2:
            positions_in_data = [pos for pos in allowed_primary_positions if
                                 pos in draft_data['Primary Position'].unique()]
            positions = ['All'] + positions_in_data
            selected_position_graph = st.selectbox("Position", positions, key="graph_position")

        # All checkboxes in one expander
        with st.expander("Show/Hide Options", expanded=False):
            draft_col, keep_col = st.columns([1, 1])
            with draft_col:
                show_drafted = st.checkbox("Drafted", value=True)
            with keep_col:
                show_keepers = st.checkbox("Keepers", value=False)

            # Position checkboxes (only for 'All')
            if selected_position_graph == 'All':
                cols = st.columns(len(positions_in_data))
                include_positions = []
                for i, pos in enumerate(positions_in_data):
                    checked = cols[i].checkbox(pos, value=True, key=f"include_{pos}")
                    if checked:
                        include_positions.append(pos)
            else:
                include_positions = None

            # Dashed line checkboxes
            if selected_manager_graph == 'League Average' and selected_position_graph == 'All':
                default_dash = True
                show_drafted_dash = st.checkbox("Show Drafted Dashed Line", value=default_dash)
                show_keepers_dash = st.checkbox("Show Keepers Dashed Line", value=default_dash)
                show_unused_dash = st.checkbox("Show Unused Dollars Dashed Line", value=default_dash)
            else:
                show_drafted_dash = False
                show_keepers_dash = False
                show_unused_dash = False

        graph_data = draft_data.copy()
        keeper_status = graph_data['Is Keeper Status']
        drafted_mask = keeper_status.isnull() | (keeper_status == 0) | (keeper_status == '') | (keeper_status == 'N/A')
        keepers_mask = keeper_status == 1

        if show_drafted and show_keepers:
            graph_data = graph_data[drafted_mask | keepers_mask]
        elif show_drafted:
            graph_data = graph_data[drafted_mask]
        elif show_keepers:
            graph_data = graph_data[keepers_mask]
        else:
            graph_data = graph_data.iloc[0:0]

        graph_data = graph_data.sort_values(['Team Manager', 'Year', 'Primary Position', 'Cost'],
                                            ascending=[True, True, True, False])
        graph_data = graph_data.loc[graph_data['Cost'] > 0]
        graph_data['RankNum'] = graph_data.groupby(['Team Manager', 'Year', 'Primary Position'])['Cost'] \
            .rank(method='first', ascending=False).astype(int)

        if selected_position_graph == 'All':
            if include_positions:
                if selected_manager_graph == 'League Average':
                    cost_by_year_pos = graph_data[graph_data['Primary Position'].isin(include_positions)] \
                        .groupby(['Year', 'Primary Position'])['Cost'].sum().reset_index()
                    cost_by_year_pos = order_positions(cost_by_year_pos, position_col='Primary Position',
                                                       allowed_positions=allowed_primary_positions)
                    cost_pivot = cost_by_year_pos.pivot(index='Year', columns='Primary Position',
                                                        values='Cost').sort_index(axis=1)
                else:
                    filtered_graph = graph_data[
                        (graph_data['Team Manager'] == selected_manager_graph) &
                        (graph_data['Primary Position'].isin(include_positions))
                        ]
                    cost_by_year_pos = filtered_graph.groupby(['Year', 'Primary Position'])['Cost'].sum().reset_index()
                    cost_by_year_pos = order_positions(cost_by_year_pos, position_col='Primary Position',
                                                       allowed_positions=allowed_primary_positions)
                    cost_pivot = cost_by_year_pos.pivot(index='Year', columns='Primary Position',
                                                        values='Cost').sort_index(axis=1)
            else:
                cost_pivot = pd.DataFrame()
        else:
            graph_data = graph_data[graph_data['Primary Position'] == selected_position_graph]
            if selected_manager_graph == 'League Average':
                avg_graph = graph_data.groupby(['Year', 'RankNum'])['Cost'].mean().reset_index()
                rank_counts = avg_graph['RankNum'].value_counts()
                common_ranks = rank_counts[rank_counts > 1].index.tolist()
                avg_graph = avg_graph[avg_graph['RankNum'].isin(common_ranks)]
                avg_graph['Cost'] = avg_graph['Cost'].round(2)
                cost_pivot = avg_graph.pivot(index='Year', columns='RankNum', values='Cost').sort_index()
            else:
                filtered_graph = graph_data[graph_data['Team Manager'] == selected_manager_graph]
                cost_by_year_rank = filtered_graph.groupby(['Year', 'RankNum'])['Cost'].mean().reset_index()
                cost_pivot = cost_by_year_rank.pivot(index='Year', columns='RankNum', values='Cost').sort_index()

        if not cost_pivot.empty:
            fig = go.Figure()
            for col in cost_pivot.columns:
                y_vals = cost_pivot[col].round(2)
                hover_texts = []
                for year in cost_pivot.index:
                    if selected_position_graph == 'All':
                        if selected_manager_graph == 'League Average':
                            rows = graph_data[(graph_data['Year'] == year) & (graph_data['Primary Position'] == col)]
                            num_managers = len(team_managers_clean)
                            total_cost_year = graph_data[graph_data['Year'] == year]['Cost'].sum()
                            avg_cost_per_manager = round(total_cost_year / num_managers, 2) if num_managers > 0 else 0

                            total_pos_cost = rows['Cost'].sum()
                            num_players_pos = len(rows)
                            avg_pos_cost = round(total_pos_cost / num_players_pos, 2) if num_players_pos > 0 else 0

                            manager_costs = rows.groupby('Team Manager')['Cost'].sum()
                            if not manager_costs.empty:
                                max_manager = manager_costs.idxmax()
                                max_manager_cost = manager_costs.max()
                            else:
                                max_manager = ""
                                max_manager_cost = 0

                            if not rows.empty:
                                max_row = rows.loc[rows['Cost'].idxmax()]
                                max_player_text = f"${max_row['Cost']}, {max_row['Name Full']}, {max_row['Team Manager']}"
                            else:
                                max_player_text = ""

                            hover_text = (
                                f"Average: ${avg_cost_per_manager}<br>"
                                f"Max Manager: {max_manager} ${max_manager_cost}<br>"
                                f"Average {col}: ${avg_pos_cost}<br>"
                                f"{col} Max: {max_player_text}"
                            )
                        else:
                            # Filter for selected manager
                            rows = graph_data[
                                (graph_data['Year'] == year) &
                                (graph_data['Primary Position'] == col) &
                                (graph_data['Team Manager'] == selected_manager_graph)
                                ]
                            total_pos_cost = rows['Cost'].sum()
                            num_players_pos = len(rows)
                            avg_pos_cost = round(total_pos_cost / num_players_pos, 2) if num_players_pos > 0 else 0
                            if not rows.empty:
                                max_row = rows.loc[rows['Cost'].idxmax()]
                                max_player_text = f"${max_row['Cost']}, {max_row['Name Full']}"
                            else:
                                max_player_text = ""
                            hover_text = (
                                f"Avg: ${avg_pos_cost}<br>"
                                f"Max: {max_player_text}"
                            )
                        hover_texts.append(hover_text)
                    elif selected_manager_graph == 'League Average' and selected_position_graph != 'All':
                        rows = graph_data[(graph_data['Year'] == year) & (graph_data['RankNum'] == col)]
                        if not rows.empty:
                            max_row = rows.loc[rows['Cost'].idxmax()]
                            min_row = rows.loc[rows['Cost'].idxmin()]
                            avg_cost = y_vals.loc[year]
                            hover_text = (
                                f"Avg: ${avg_cost}<br>"
                                f"Max: ${max_row['Cost']}, {max_row['Name Full']}, {max_row['Team Manager']}<br>"
                                f"Min: ${min_row['Cost']}, {min_row['Name Full']}, {min_row['Team Manager']}"
                            )
                        else:
                            hover_text = ""
                        hover_texts.append(hover_text)
                    elif selected_manager_graph != 'League Average' and selected_position_graph != 'All':
                        filtered_graph = graph_data[graph_data['Team Manager'] == selected_manager_graph]
                        player_row = filtered_graph[
                            (filtered_graph['Year'] == year) & (filtered_graph['RankNum'] == col)
                            ]
                        if not player_row.empty and 'Name Full' in player_row.columns:
                            hover_texts.append(player_row.iloc[0]['Name Full'])
                        else:
                            hover_texts.append('')
                    else:
                        hover_texts = None  # No hover text for this case

                fig.add_trace(go.Scatter(
                    x=cost_pivot.index, y=y_vals,
                    mode='lines+markers', name=str(col),
                    text=hover_texts if hover_texts is not None else None,
                    hovertemplate='%{text}<extra></extra>' if hover_texts is not None else None
                ))

            # Dashed lines based on selected manager
            if selected_position_graph == 'All':
                if selected_manager_graph == 'League Average':
                    num_managers = draft_data['Team Manager'].nunique()
                    drafted_sum = graph_data[drafted_mask].groupby('Year')['Cost'].sum().round(2)
                    keepers_sum = graph_data[keepers_mask].groupby('Year')['Cost'].sum().round(2)
                    unused_dollars = (num_managers * 200 - drafted_sum - keepers_sum).round(2)
                else:
                    manager_graph_data = graph_data[graph_data['Team Manager'] == selected_manager_graph]
                    drafted_sum = manager_graph_data[drafted_mask].groupby('Year')['Cost'].sum().round(2)
                    keepers_sum = manager_graph_data[keepers_mask].groupby('Year')['Cost'].sum().round(2)
                    unused_dollars = (200 - drafted_sum - keepers_sum).round(2)

                if show_drafted and show_drafted_dash and not drafted_sum.empty:
                    fig.add_trace(go.Scatter(
                        x=drafted_sum.index, y=drafted_sum.values,
                        mode='lines+markers', name='Drafted Dashed',
                        line=dict(dash='dash', color='blue')
                    ))
                if show_keepers and show_keepers_dash and not keepers_sum.empty:
                    fig.add_trace(go.Scatter(
                        x=keepers_sum.index, y=keepers_sum.values,
                        mode='lines+markers', name='Keepers Dashed',
                        line=dict(dash='dash', color='red')
                    ))
                if show_unused_dash and not unused_dollars.empty:
                    fig.add_trace(go.Scatter(
                        x=unused_dollars.index, y=unused_dollars.values,
                        mode='lines+markers', name='Unused Dollars',
                        line=dict(dash='dash', color='green')
                    ))
            else:
                if selected_manager_graph == 'League Average':
                    drafted_sum = graph_data[drafted_mask].groupby('Year')['Cost'].sum().round(2)
                    keepers_sum = graph_data[keepers_mask].groupby('Year')['Cost'].sum().round(2)
                else:
                    manager_graph_data = graph_data[graph_data['Team Manager'] == selected_manager_graph]
                    drafted_sum = manager_graph_data[drafted_mask].groupby('Year')['Cost'].sum().round(2)
                    keepers_sum = manager_graph_data[keepers_mask].groupby('Year')['Cost'].sum().round(2)

                if show_drafted and show_drafted_dash and not drafted_sum.empty:
                    fig.add_trace(go.Scatter(
                        x=drafted_sum.index, y=drafted_sum.values,
                        mode='lines+markers', name='Drafted Dashed',
                        line=dict(dash='dash', color='blue')
                    ))
                if show_keepers and show_keepers_dash and not keepers_sum.empty:
                    fig.add_trace(go.Scatter(
                        x=keepers_sum.index, y=keepers_sum.values,
                        mode='lines+markers', name='Keepers Dashed',
                        line=dict(dash='dash', color='red')
                    ))
                # No unused dollars line for positions other than 'All'

            fig.update_layout(title="Cost Over Time", xaxis_title="Year", yaxis_title="Cost")
            st.plotly_chart(fig)