import streamlit as st
import pandas as pd

def display_scoring_outcomes(draft_data, player_df):
    st.header("Scoring Outcomes")

    # Convert 'Year', 'Team Manager', and 'season' columns to strings to avoid comparison issues
    draft_data['Year'] = draft_data['Year'].astype(str)
    draft_data['Team Manager'] = draft_data['Team Manager'].astype(str)
    player_df['season'] = player_df['season'].astype(str)

    # Check if 'position' column exists in player_df
    if 'position' not in player_df.columns:
        st.error("The 'position' column is missing from player_df.")
        return

    # Dropdowns for Year, Team Manager, and Primary Position
    years = sorted(draft_data['Year'].unique().tolist())
    team_managers = sorted(draft_data['Team Manager'].unique().tolist())
    allowed_primary_positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
    primary_positions = [pos for pos in sorted(player_df['position'].unique().tolist()) if pos in allowed_primary_positions]

    # Search bar for player
    col1, col2 = st.columns([1, 1])
    with col1:
        search_players = st.multiselect("Search Player", options=player_df['player'].unique().tolist(), default=[])
    with col2:
        selected_team_managers = st.multiselect("Select Team Manager", team_managers, default=[])

    col3, col4 = st.columns([1, 1])
    with col3:
        selected_years = st.multiselect("Select Year", years, default=[])
    with col4:
        selected_primary_positions = st.multiselect("Select Primary Position", primary_positions, default=[])

    # Checkboxes for Include Drafted and Include Keepers
    col5, col6 = st.columns([1, 1])
    with col5:
        include_drafted = st.checkbox("Include Drafted", value=True, key="include_drafted")
    with col6:
        include_keepers = st.checkbox("Include Keepers", value=True, key="include_keepers")

    # Filter the draft data based on the selected year and team manager
    if selected_years:
        draft_data = draft_data[draft_data['Year'].isin(selected_years)]
        player_df = player_df[player_df['playeryear'].str.contains('|'.join(selected_years))]
    if selected_team_managers:
        draft_data = draft_data[draft_data['Team Manager'].isin(selected_team_managers)]

    # Merge draft_data with player_df to get points and position from player_df
    merged_data = draft_data.merge(player_df[['playeryear', 'player', 'points', 'week', 'season', 'position']], left_on=['Name Full', 'Year'], right_on=['player', 'season'], how='left')

    # Filter merged data to only include weeks up to 16 if year is prior to 2021 and up to 17 if 2021 or later
    merged_data = merged_data[(merged_data['Year'].astype(int) < 2021) & (merged_data['week'] <= 16) | (merged_data['Year'].astype(int) >= 2021) & (merged_data['week'] <= 17)]

    # Filter based on Keeper status
    if include_drafted and not include_keepers:
        merged_data = merged_data[merged_data['Is Keeper Status'] != 1]
    elif not include_drafted and include_keepers:
        merged_data = merged_data[merged_data['Is Keeper Status'] == 1]
    elif not include_drafted and not include_keepers:
        merged_data = pd.DataFrame()  # Empty DataFrame if neither is selected

    # Aggregate data by season, player, and position from player_df
    aggregated_data = merged_data.groupby(['season', 'player', 'position']).agg({
        'points': 'sum',
        'Cost': 'first',
        'Pick': 'first',
        'Name Full': 'first',
        'Team Manager': 'first',
        'week': pd.Series.nunique  # Count unique weeks
    }).reset_index()

    # Calculate PPG (Points Per Game)
    aggregated_data['PPG'] = (aggregated_data['points'] / aggregated_data['week']).round(2)

    # Rank each position by 'Cost', 'Total Points', and 'PPG' for each 'season'
    aggregated_data['Rank by Cost'] = aggregated_data.groupby(['season', 'position'])['Cost'].rank(method='first', ascending=False).astype(int)
    aggregated_data['Rank by Total Points'] = aggregated_data.groupby(['season', 'position'])['points'].rank(method='first', ascending=False).astype(int)
    aggregated_data['Rank by PPG'] = aggregated_data.groupby(['season', 'position'])['PPG'].rank(method='first', ascending=False).astype(int)

    # Create columns with position rank like RB1, RB2, etc.
    aggregated_data['Cost Rank'] = aggregated_data['position'] + aggregated_data['Rank by Cost'].astype(str)
    aggregated_data['Total Points Rank'] = aggregated_data['position'] + aggregated_data['Rank by Total Points'].astype(str)
    aggregated_data['PPG Rank'] = aggregated_data['position'] + aggregated_data['Rank by PPG'].astype(str)

    # Rename columns for clarity
    aggregated_data.rename(columns={'points': 'Total Points', 'Name Full': 'Player', 'week': 'Unique Weeks'}, inplace=True)

    # Filter aggregated data to only include allowed primary positions
    aggregated_data = aggregated_data[aggregated_data['position'].isin(allowed_primary_positions)]

    # Filter the aggregated data based on the selected primary position
    if selected_primary_positions:
        aggregated_data = aggregated_data[aggregated_data['position'].isin(selected_primary_positions)]

    # Filter by player search
    if search_players:
        aggregated_data = aggregated_data[aggregated_data['player'].isin(search_players)]

    # Sort the position rank columns correctly
    def sort_position_rank(rank):
        position, number = rank[:-1], rank[-1:]
        return (position, int(number))

    aggregated_data = aggregated_data.sort_values(by=['Cost Rank'], key=lambda x: x.map(sort_position_rank))
    aggregated_data = aggregated_data.sort_values(by=['Total Points Rank'], key=lambda x: x.map(sort_position_rank))
    aggregated_data = aggregated_data.sort_values(by=['PPG Rank'], key=lambda x: x.map(sort_position_rank))

    # Select and display the specified columns, hiding the 'Pick' column
    columns_to_display = ['season', 'Player', 'position', 'Cost Rank', 'Total Points Rank', 'PPG Rank', 'Total Points', 'PPG', 'Cost', 'Team Manager']
    st.dataframe(aggregated_data[columns_to_display], hide_index=True)