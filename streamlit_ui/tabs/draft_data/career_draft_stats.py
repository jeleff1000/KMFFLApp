import streamlit as st
import pandas as pd
import numpy as np

def display_career_draft(draft_data):
    st.header("Career Draft Stats")

    # Convert 'Team Manager' and 'Year' columns to strings to avoid comparison issues
    draft_data['Team Manager'] = draft_data['Team Manager'].astype(str)
    draft_data['Year'] = draft_data['Year'].astype(str)

    # Filter out rows where 'Team Manager' is "nan"
    draft_data = draft_data[draft_data['Team Manager'] != "nan"]

    # Convert 'Name Full' to lowercase for case-insensitive aggregation
    draft_data['Name Full'] = draft_data['Name Full'].str.lower()

    # Dropdowns for Team Manager and Primary Position
    col1, col2 = st.columns(2)
    with col1:
        team_managers = sorted(draft_data['Team Manager'].unique().tolist())
        selected_team_managers = st.multiselect("Select Team Manager", options=team_managers, default=[], key='team_manager')
    with col2:
        primary_positions = sorted(draft_data['Primary Position'].unique().tolist())
        selected_primary_positions = st.multiselect("Select Primary Position", options=primary_positions, default=[], key='primary_position')

    # Searchable dropdown for Name Full
    names_full = sorted(draft_data['Name Full'].unique().tolist())
    selected_names_full = st.multiselect("Search Name Full", options=names_full, default=[], key='name_full')

    # Filter the draft data based on the selected team managers, primary positions, and names full
    if selected_team_managers:
        draft_data = draft_data[draft_data['Team Manager'].isin(selected_team_managers)]
    if selected_primary_positions:
        draft_data = draft_data[draft_data['Primary Position'].isin(selected_primary_positions)]
    if selected_names_full:
        draft_data = draft_data[draft_data['Name Full'].isin(selected_names_full)]

    # Create a new column 'Times Drafted' to count unique years where 'Pick' is at least 1
    draft_data['Times Drafted'] = draft_data.apply(lambda row: 1 if row['Pick'] >= 1 else 0, axis=1)

    # Aggregate data by 'Name Full' and 'Primary Position'
    aggregated_data = draft_data.groupby(['Name Full', 'Primary Position']).agg({
        'Cost': 'sum',
        'Is Keeper Status': 'sum',
        'Is Keeper Cost': 'sum',
        'Times Drafted': 'sum'
    }).reset_index()

    # Capitalize each name in the display
    aggregated_data['Name Full'] = aggregated_data['Name Full'].str.title()

    # Select and display the specified columns
    columns_to_display = ['Name Full', 'Primary Position', 'Cost', 'Is Keeper Status', 'Is Keeper Cost', 'Times Drafted']
    st.dataframe(aggregated_data[columns_to_display], hide_index=True)