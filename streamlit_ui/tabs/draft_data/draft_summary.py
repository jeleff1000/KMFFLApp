import streamlit as st
import pandas as pd

def display_draft_summary(draft_data):
    st.header("Draft Summary")

    # Convert 'Team Manager' and 'Year' columns to strings to avoid comparison issues
    draft_data['Team Manager'] = draft_data['Team Manager'].astype(str)
    draft_data['Year'] = draft_data['Year'].astype(str)

    # Filter out rows where 'Team Manager' is "nan"
    draft_data = draft_data[draft_data['Team Manager'] != "nan"]

    # Add "All" option to the dropdown lists
    team_managers = sorted(draft_data['Team Manager'].unique().tolist())
    years = sorted(draft_data['Year'].unique().tolist())

    # Create columns for search bar and dropdowns
    col1, col2 = st.columns([1, 1])
    with col1:
        search_names = st.multiselect("Search Player", options=draft_data['Name Full'].unique().tolist(), default=[])
    with col2:
        selected_team_managers = st.multiselect("Select Team Manager(s)", team_managers, default=[])

    # Create columns for year selection and checkboxes
    col3, col4 = st.columns([1, 1])
    with col3:
        selected_years = st.multiselect("Select Year(s)", years, default=[])
    with col4:
        include_drafted = st.checkbox("Include Drafted", value=True)
        include_keepers = st.checkbox("Include Keepers", value=True)

    # Filter the draft data based on selections
    if search_names:
        draft_data = draft_data[draft_data['Name Full'].isin(search_names)]
    if selected_team_managers:
        draft_data = draft_data[draft_data['Team Manager'].isin(selected_team_managers)]
    if selected_years:
        draft_data = draft_data[draft_data['Year'].isin(selected_years)]

    # Filter based on Keeper status
    if not include_drafted:
        draft_data = draft_data[draft_data['Is Keeper Status'] != 0]
    if not include_keepers:
        draft_data = draft_data[draft_data['Is Keeper Status'] != 1]

    # Ensure players with no value in Keeper status only show up if Include Drafted is checked
    if not include_drafted:
        draft_data = draft_data[draft_data['Is Keeper Status'].notna()]

    # Rename 'Is Keeper Status' to 'Keeper' and convert to boolean
    draft_data['Keeper'] = draft_data['Is Keeper Status'].apply(lambda x: True if x == 1 else False)

    # Convert 'Percent Drafted' to numeric and format as a whole number percentage
    draft_data['Percent Drafted'] = pd.to_numeric(draft_data['Percent Drafted'], errors='coerce')
    draft_data['Percent Drafted'] = draft_data['Percent Drafted'].apply(lambda x: f"{int(x * 100)}%" if pd.notnull(x) else "NaN")

    # Select and display the specified columns
    columns_to_display = [
        'Team Manager', 'Name Full', 'Primary Position', 'Round', 'Pick',
        'Cost', 'Average Cost', 'Savings', 'Average Round', 'Average Pick', 'Percent Drafted', 'Keeper'
    ]
    st.dataframe(draft_data[columns_to_display], hide_index=True)