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

def display_cost_over_time_graph(draft_data, allowed_primary_positions=None, unique_prefix=""):
    if allowed_primary_positions is None:
        allowed_primary_positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    # Initial clean
    draft_data = draft_data.copy()
    draft_data['manager'] = (
        draft_data['manager']
        .fillna('Blank')
        .replace(['', 'nan', pd.NA], 'Blank')
    )

    st.subheader("cost Over Time")
    col1, col2 = st.columns(2)
    team_managers_clean = [m for m in draft_data['manager'].unique() if m != 'League Total']
    team_managers = ['League Average'] + sorted(team_managers_clean)
    with col1:
        selected_manager_graph = st.selectbox(
            "Manager", team_managers, index=0, key=f"{unique_prefix}_graph_manager"
        )
    with col2:
        positions_in_data = [pos for pos in allowed_primary_positions if
                             pos in draft_data['primary_position'].unique()]
        positions = ['All'] + positions_in_data
        selected_position_graph = st.selectbox(
            "Position", positions, key=f"{unique_prefix}_graph_position"
        )

    with st.expander("Show/Hide Options", expanded=False):
        draft_col, keep_col = st.columns([1, 1])
        with draft_col:
            show_drafted = st.checkbox("Drafted", value=True, key=f"{unique_prefix}_show_drafted")
        with keep_col:
            show_keepers = st.checkbox("Keepers", value=True, key=f"{unique_prefix}_show_keepers")

        if selected_position_graph == 'All':
            cols = st.columns(len(positions_in_data))
            include_positions = []
            for i, pos in enumerate(positions_in_data):
                checked = cols[i].checkbox(
                    pos, value=True, key=f"{unique_prefix}_include_{pos}"
                )
                if checked:
                    include_positions.append(pos)
        else:
            include_positions = None

        default_dash = selected_manager_graph == "League Average"
        show_drafted_dash = st.checkbox(
            "Show Total Drafted Line", value=default_dash, key=f"{unique_prefix}_show_drafted_dash"
        )
        show_keepers_dash = st.checkbox(
            "Show Total Keepers Line", value=default_dash, key=f"{unique_prefix}_show_keepers_dash"
        )
        show_unused_dash = st.checkbox(
            "Show Total Unused Dollars Line", value=default_dash, key=f"{unique_prefix}_show_unused_dash"
        )

    # Clean after copy/filter
    graph_data = draft_data.copy()
    graph_data['manager'] = (
        graph_data['manager']
        .fillna('Blank')
        .replace(['', 'nan', pd.NA], 'Blank')
    )

    keeper_status = graph_data['is_keeper_status']
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

    # Clean again after filtering
    graph_data['manager'] = (
        graph_data['manager']
        .fillna('Blank')
        .replace(['', 'nan', pd.NA], 'Blank')
    )

    graph_data = graph_data.sort_values(['manager', 'year', 'primary_position', 'cost'],
                                        ascending=[True, True, True, False])
    graph_data = graph_data.loc[graph_data['cost'] > 0]
    graph_data['RankNum'] = graph_data.groupby(['manager', 'year', 'primary_position'])['cost'] \
        .rank(method='first', ascending=False).astype(int)

    if selected_position_graph == 'All':
        if include_positions:
            if selected_manager_graph == 'League Average':
                cost_by_year_pos = graph_data[graph_data['primary_position'].isin(include_positions)] \
                    .groupby(['year', 'primary_position'])['cost'].sum().reset_index()
                cost_by_year_pos = order_positions(cost_by_year_pos, position_col='primary_position',
                                                   allowed_positions=allowed_primary_positions)
                cost_pivot = cost_by_year_pos.pivot(index='year', columns='primary_position',
                                                    values='cost').sort_index(axis=1)
            else:
                filtered_graph = graph_data[
                    (graph_data['manager'] == selected_manager_graph) &
                    (graph_data['primary_position'].isin(include_positions))
                    ].copy()
                filtered_graph['manager'] = (
                    filtered_graph['manager']
                    .fillna('Blank')
                    .replace(['', 'nan', pd.NA], 'Blank')
                )
                cost_by_year_pos = filtered_graph.groupby(['year', 'primary_position'])['cost'].sum().reset_index()
                cost_by_year_pos = order_positions(cost_by_year_pos, position_col='primary_position',
                                                   allowed_positions=allowed_primary_positions)
                cost_pivot = cost_by_year_pos.pivot(index='year', columns='primary_position',
                                                    values='cost').sort_index(axis=1)
        else:
            cost_pivot = pd.DataFrame()
    else:
        graph_data = graph_data[graph_data['primary_position'] == selected_position_graph].copy()
        graph_data['manager'] = (
            graph_data['manager']
            .fillna('Blank')
            .replace(['', 'nan', pd.NA], 'Blank')
        )
        if selected_manager_graph == 'League Average':
            avg_graph = graph_data.groupby(['year', 'RankNum'])['cost'].mean().reset_index()
            rank_counts = avg_graph['RankNum'].value_counts()
            common_ranks = rank_counts[rank_counts > 1].index.tolist()
            avg_graph = avg_graph[avg_graph['RankNum'].isin(common_ranks)]
            avg_graph['cost'] = avg_graph['cost'].round(2)
            cost_pivot = avg_graph.pivot(index='year', columns='RankNum', values='cost').sort_index()
        else:
            filtered_graph = graph_data[graph_data['manager'] == selected_manager_graph].copy()
            filtered_graph['manager'] = (
                filtered_graph['manager']
                .fillna('Blank')
                .replace(['', 'nan', pd.NA], 'Blank')
            )
            cost_by_year_rank = filtered_graph.groupby(['year', 'RankNum'])['cost'].mean().reset_index()
            cost_pivot = cost_by_year_rank.pivot(index='year', columns='RankNum', values='cost').sort_index()



    if not cost_pivot.empty:
        fig = go.Figure()
        for col in cost_pivot.columns:
            y_vals = cost_pivot[col].round(2)
            hover_texts = []
            for year in cost_pivot.index:
                if selected_position_graph == 'All':
                    if selected_manager_graph == 'League Average':
                        rows = graph_data[(graph_data['year'] == year) & (graph_data['primary_position'] == col)]
                        num_managers = len(team_managers_clean)
                        total_cost_year = graph_data[graph_data['year'] == year]['cost'].sum()
                        avg_cost_per_manager = round(total_cost_year / num_managers, 2) if num_managers > 0 else 0

                        total_pos_cost = rows['cost'].sum()
                        num_players_pos = len(rows)
                        avg_pos_cost = round(total_pos_cost / num_players_pos, 2) if num_players_pos > 0 else 0

                        manager_costs = rows.groupby('manager')['cost'].sum()
                        if not manager_costs.empty:
                            max_manager = manager_costs.idxmax()
                            max_manager_cost = manager_costs.max()
                        else:
                            max_manager = ""
                            max_manager_cost = 0

                        if not rows.empty:
                            max_row = rows.loc[rows['cost'].idxmax()]
                            max_player_text = f"${max_row['cost']}, {max_row['player_name']}, {max_row['manager']}"
                        else:
                            max_player_text = ""

                        hover_text = (
                            f"Average: ${avg_cost_per_manager}<br>"
                            f"Max Manager: {max_manager} ${max_manager_cost}<br>"
                            f"Average {col}: ${avg_pos_cost}<br>"
                            f"{col} Max: {max_player_text}"
                        )
                    else:
                        rows = graph_data[
                            (graph_data['year'] == year) &
                            (graph_data['primary_position'] == col) &
                            (graph_data['manager'] == selected_manager_graph)
                            ]
                        total_pos_cost = rows['cost'].sum()
                        num_players_pos = len(rows)
                        avg_pos_cost = round(total_pos_cost / num_players_pos, 2) if num_players_pos > 0 else 0
                        if not rows.empty:
                            max_row = rows.loc[rows['cost'].idxmax()]
                            max_player_text = f"${max_row['cost']}, {max_row['player_name']}"
                        else:
                            max_player_text = ""
                        hover_text = (
                            f"Avg: ${avg_pos_cost}<br>"
                            f"Max: {max_player_text}"
                        )
                    hover_texts.append(hover_text)
                elif selected_manager_graph == 'League Average' and selected_position_graph != 'All':
                    rows = graph_data[(graph_data['year'] == year) & (graph_data['RankNum'] == col)]
                    if not rows.empty:
                        max_row = rows.loc[rows['cost'].idxmax()]
                        min_row = rows.loc[rows['cost'].idxmin()]
                        avg_cost = y_vals.loc[year]
                        hover_text = (
                            f"Avg: ${avg_cost}<br>"
                            f"Max: ${max_row['cost']}, {max_row['player_name']}, {max_row['manager']}<br>"
                            f"Min: ${min_row['cost']}, {min_row['player_name']}, {min_row['manager']}"
                        )
                    else:
                        hover_text = ""
                    hover_texts.append(hover_text)
                elif selected_manager_graph != 'League Average' and selected_position_graph != 'All':
                    filtered_graph = graph_data[graph_data['manager'] == selected_manager_graph]
                    player_row = filtered_graph[
                        (filtered_graph['year'] == year) & (filtered_graph['RankNum'] == col)
                        ]
                    if not player_row.empty and 'player_name' in player_row.columns and 'cost' in player_row.columns:
                        hover_texts.append(f"{player_row.iloc[0]['player_name']}, ${player_row.iloc[0]['cost']}")
                    else:
                        hover_texts.append('')
                else:
                    hover_texts = None

            fig.add_trace(go.Scatter(
                x=cost_pivot.index, y=y_vals,
                mode='lines+markers', name=str(col),
                text=hover_texts if hover_texts is not None else None,
                hovertemplate='%{text}<extra></extra>' if hover_texts is not None else None
            ))

            # Dashed lines for all managers
            if selected_position_graph == 'All':
                if selected_manager_graph == 'League Average':
                    drafted_sum = graph_data[drafted_mask].groupby('year')['cost'].sum().round(2)
                    keepers_sum = graph_data[keepers_mask].groupby('year')['cost'].sum().round(2)
                    unused_dollars = pd.Series(dtype=float)
                    for year in drafted_sum.index:
                        managers_in_year = draft_data.loc[
                            (draft_data['year'] == year) &
                            ~draft_data['manager'].isin(['Blank', 'nan', pd.NA, 'League Total']),
                            'manager'
                        ].nunique()
                        unused_dollars.loc[year] = (
                                    managers_in_year * 200 - drafted_sum.loc[year] - keepers_sum.get(year, 0))
                    unused_dollars = unused_dollars.round(2)
                else:
                    manager_graph_data = graph_data[graph_data['manager'] == selected_manager_graph]
                    drafted_sum = manager_graph_data[drafted_mask].groupby('year')['cost'].sum().round(2)
                    keepers_sum = manager_graph_data[keepers_mask].groupby('year')['cost'].sum().round(2)
                    unused_dollars = (200 - drafted_sum - keepers_sum).round(2)

                if show_drafted and show_drafted_dash and not drafted_sum.empty:
                    fig.add_trace(go.Scatter(
                        x=drafted_sum.index, y=drafted_sum.values,
                        mode='lines+markers', name='Drafted Total',
                        line=dict(dash='dash', color='blue')
                    ))
                if show_keepers and show_keepers_dash and not keepers_sum.empty:
                    fig.add_trace(go.Scatter(
                        x=keepers_sum.index, y=keepers_sum.values,
                        mode='lines+markers', name='Keepers Total',
                        line=dict(dash='dash', color='red')
                    ))
                if show_unused_dash and not unused_dollars.empty:
                    fig.add_trace(go.Scatter(
                        x=unused_dollars.index, y=unused_dollars.values,
                        mode='lines+markers', name='Unused Dollars',
                        line=dict(dash='dash', color='green')
                    ))
            if show_keepers and show_keepers_dash and not keepers_sum.empty:
                fig.add_trace(go.Scatter(
                    x=keepers_sum.index, y=keepers_sum.values,
                    mode='lines+markers', name='Keepers Total',
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
                # Use mean instead of sum for League Average when position != 'All'
                drafted_mean = graph_data[drafted_mask].groupby('year')['cost'].mean().round(2)
                keepers_mean = graph_data[keepers_mask].groupby('year')['cost'].mean().round(2)
            else:
                manager_graph_data = graph_data[graph_data['manager'] == selected_manager_graph]
                drafted_mean = manager_graph_data[drafted_mask].groupby('year')['cost'].mean().round(2)
                keepers_mean = manager_graph_data[keepers_mask].groupby('year')['cost'].mean().round(2)

            if show_drafted and show_drafted_dash and not drafted_mean.empty:
                fig.add_trace(go.Scatter(
                    x=drafted_mean.index, y=drafted_mean.values,
                    mode='lines+markers', name='Drafted Total',
                    line=dict(dash='dash', color='blue')
                ))
            if show_keepers and show_keepers_dash and not keepers_mean.empty:
                fig.add_trace(go.Scatter(
                    x=keepers_mean.index, y=keepers_mean.values,
                    mode='lines+markers', name='Keepers Total',
                    line=dict(dash='dash', color='red')
                ))
            # No unused dollars line for positions other than 'All'

        fig.update_layout(title="cost Over Time", xaxis_title="year", yaxis_title="cost")
        st.plotly_chart(fig)