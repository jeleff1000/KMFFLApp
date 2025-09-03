import streamlit as st
import pandas as pd

def display_draft_summary(draft_data):
    st.header("Draft Summary")

    draft_data['Team Manager'] = draft_data['Team Manager'].astype(str)
    draft_data['Year'] = draft_data['Year'].astype(str)
    draft_data = draft_data[draft_data['Team Manager'] != "nan"]

    team_managers = sorted(draft_data['Team Manager'].unique().tolist())
    years = sorted(draft_data['Year'].unique().tolist())

    # Desired order for positions
    desired_order = ['QB', 'RB', 'WR', 'TE', 'DEF', 'K']
    all_positions = draft_data['Primary Position'].dropna().unique().tolist()
    # Sort positions: desired first, then any others alphabetically
    positions = [pos for pos in desired_order if pos in all_positions] + sorted([pos for pos in all_positions if pos not in desired_order])

    # Top row: search and manager selection
    col1, col2 = st.columns([1, 1])
    with col1:
        search_names = st.multiselect("Search Player", options=draft_data['Name Full'].unique().tolist(), default=[])
    with col2:
        selected_team_managers = st.multiselect("Select Team Manager(s)", team_managers, default=[])

    # Second row: year and position selection
    col3, col4 = st.columns([1, 1])
    with col3:
        selected_years = st.multiselect("Select Year(s)", years, default=[])
    with col4:
        selected_positions = st.multiselect("Select Primary Position(s)", positions, default=[])

    # Third row: checkboxes
    col5, col6 = st.columns([1, 1])
    with col5:
        include_drafted = st.checkbox("Include Drafted", value=True)
    with col6:
        include_keepers = st.checkbox("Include Keepers", value=True)

    # Filtering logic
    if search_names:
        draft_data = draft_data[draft_data['Name Full'].isin(search_names)]
    if selected_team_managers:
        draft_data = draft_data[draft_data['Team Manager'].isin(selected_team_managers)]
    if selected_years:
        draft_data = draft_data[draft_data['Year'].isin(selected_years)]
    if selected_positions:
        draft_data = draft_data[draft_data['Primary Position'].isin(selected_positions)]

    if not include_drafted:
        draft_data = draft_data[draft_data['Is Keeper Status'] != 0]
    if not include_keepers:
        draft_data = draft_data[draft_data['Is Keeper Status'] != 1]
    if not include_drafted:
        draft_data = draft_data[draft_data['Is Keeper Status'].notna()]

    draft_data['Keeper'] = draft_data['Is Keeper Status'].apply(lambda x: True if x == 1 else False)
    draft_data['Percent Drafted'] = pd.to_numeric(draft_data['Percent Drafted'], errors='coerce')
    draft_data['Percent Drafted'] = draft_data['Percent Drafted'].apply(lambda x: f"{int(x * 100)}%" if pd.notnull(x) else "NaN")

    columns_to_display = [
        'Year', 'Team Manager', 'Name Full', 'Primary Position', 'Round', 'Pick',
        'Cost', 'Average Cost', 'Savings', 'Average Round', 'Average Pick', 'Percent Drafted', 'Keeper'
    ]
    st.dataframe(draft_data[columns_to_display], hide_index=True)