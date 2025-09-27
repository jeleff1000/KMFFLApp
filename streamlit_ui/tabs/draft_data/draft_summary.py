import streamlit as st
import pandas as pd

def display_draft_summary(draft_data):
    st.header("Draft Summary")

    draft_data['manager'] = draft_data['manager'].astype(str)
    draft_data['year'] = draft_data['year'].astype(str)
    draft_data = draft_data[draft_data['manager'] != "nan"]

    team_managers = sorted(draft_data['manager'].unique().tolist())
    years = sorted(draft_data['year'].unique().tolist())

    # Desired order for positions
    desired_order = ['QB', 'RB', 'WR', 'TE', 'DEF', 'K']
    all_positions = draft_data['primary_position'].dropna().unique().tolist()
    # Sort positions: desired first, then any others alphabetically
    positions = [pos for pos in desired_order if pos in all_positions] + sorted([pos for pos in all_positions if pos not in desired_order])

    # Top row: search and manager selection
    col1, col2 = st.columns([1, 1])
    with col1:
        search_names = st.multiselect("Search Player", options=draft_data['player_name'].unique().tolist(), default=[])
    with col2:
        selected_team_managers = st.multiselect("Select manager(s)", team_managers, default=[])

    # Second row: year and position selection
    col3, col4 = st.columns([1, 1])
    with col3:
        selected_years = st.multiselect("Select year(s)", years, default=[])
    with col4:
        selected_positions = st.multiselect("Select primary_position(s)", positions, default=[])

    # Third row: checkboxes
    col5, col6 = st.columns([1, 1])
    with col5:
        include_drafted = st.checkbox("Include Drafted", value=True)
    with col6:
        include_keepers = st.checkbox("Include Keepers", value=True)

    # Filtering logic
    if search_names:
        draft_data = draft_data[draft_data['player_name'].isin(search_names)]
    if selected_team_managers:
        draft_data = draft_data[draft_data['manager'].isin(selected_team_managers)]
    if selected_years:
        draft_data = draft_data[draft_data['year'].isin(selected_years)]
    if selected_positions:
        draft_data = draft_data[draft_data['primary_position'].isin(selected_positions)]

    if not include_drafted:
        draft_data = draft_data[draft_data['is_keeper_status'] != 0]
    if not include_keepers:
        draft_data = draft_data[draft_data['is_keeper_status'] != 1]
    if not include_drafted:
        draft_data = draft_data[draft_data['is_keeper_status'].notna()]

    draft_data['Keeper'] = draft_data['is_keeper_status'].apply(lambda x: True if x == 1 else False)
    draft_data['percent_drafted'] = pd.to_numeric(draft_data['percent_drafted'], errors='coerce')
    draft_data['percent_drafted'] = draft_data['percent_drafted'].apply(lambda x: f"{int(x * 100)}%" if pd.notnull(x) else "NaN")

    columns_to_display = [
        'year', 'manager', 'player_name', 'primary_position', 'round', 'pick',
        'cost', 'avg_cost', 'savings', 'avg_round', 'avg_pick', 'percent_drafted', 'is_keeper_status'
    ]
    st.dataframe(draft_data[columns_to_display], hide_index=True)