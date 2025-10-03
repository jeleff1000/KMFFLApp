import streamlit as st
import pandas as pd
import numpy as np

def display_career_draft(draft_data):
    st.header("Career Draft Stats")

    # Standardize column names to snake_case
    draft_data = draft_data.rename(columns={
        'Team Manager': 'manager',
        'Year': 'year',
        'Name Full': 'player_name',
        'Primary Position': 'primary_position',
        'Cost': 'cost',
        'Is Keeper Status': 'is_keeper_status',
        'Is Keeper Cost': 'is_keeper_cost',
        'Pick': 'pick'
    })

    draft_data['manager'] = draft_data['manager'].astype(str)
    draft_data['year'] = draft_data['year'].astype(str)
    draft_data = draft_data[draft_data['manager'] != "nan"]
    draft_data['player_name'] = draft_data['player_name'].str.lower()

    col1, col2 = st.columns(2)
    with col1:
        team_managers = sorted(draft_data['manager'].unique().tolist())
        selected_team_managers = st.multiselect("Select Manager", options=team_managers, default=[], key='manager')
    with col2:
        primary_positions = sorted([pos for pos in draft_data['primary_position'].unique().tolist() if pos is not None])
        selected_primary_positions = st.multiselect("Select Primary Position", options=primary_positions, default=[], key='primary_position')

    names_full = sorted([name for name in draft_data['player_name'].unique().tolist() if name is not None])
    selected_names_full = st.multiselect("Search Player Name", options=names_full, default=[], key='player_name')

    if selected_team_managers:
        draft_data = draft_data[draft_data['manager'].isin(selected_team_managers)]
    if selected_primary_positions:
        draft_data = draft_data[draft_data['primary_position'].isin(selected_primary_positions)]
    if selected_names_full:
        draft_data = draft_data[draft_data['player_name'].isin(selected_names_full)]

    draft_data['times_drafted'] = draft_data.apply(lambda row: 1 if row.get('pick', 0) >= 1 else 0, axis=1)

    aggregated_data = draft_data.groupby(['player_name', 'primary_position']).agg({
        'cost': 'sum',
        'is_keeper_status': 'sum',
        'is_keeper_cost': 'sum',
        'times_drafted': 'sum'
    }).reset_index()

    aggregated_data['player_name'] = aggregated_data['player_name'].str.title()

    columns_to_display = [
        'player_name', 'primary_position', 'cost', 'is_keeper_status', 'is_keeper_cost', 'times_drafted'
    ]
    columns_present = [col for col in columns_to_display if col in aggregated_data.columns]
    st.dataframe(aggregated_data[columns_present], hide_index=True)