import streamlit as st
import pandas as pd

def display_scoring_outcomes(draft_data, player_df):
    st.header("Scoring Outcomes")

    draft_data['Year'] = draft_data['Year'].astype(str)
    draft_data['Team Manager'] = draft_data['Team Manager'].astype(str)
    player_df['season'] = player_df['season'].astype(str)

    if 'position' not in player_df.columns:
        st.error("The 'position' column is missing from player_df.")
        return

    years = sorted(draft_data['Year'].unique().tolist())
    team_managers = sorted(draft_data['Team Manager'].unique().tolist())
    allowed_primary_positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
    primary_positions = [pos for pos in sorted(player_df['position'].unique().tolist()) if pos in allowed_primary_positions]

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

    col5, col6 = st.columns([1, 1])
    with col5:
        include_drafted = st.checkbox("Include Drafted", value=True, key="include_drafted")
    with col6:
        include_keepers = st.checkbox("Include Keepers", value=True, key="include_keepers")

    if selected_years:
        draft_data = draft_data[draft_data['Year'].isin(selected_years)]
        player_df = player_df[player_df['playeryear'].str.contains('|'.join(selected_years))]
    if selected_team_managers:
        draft_data = draft_data[draft_data['Team Manager'].isin(selected_team_managers)]

    merged_data = draft_data.merge(
        player_df[['playeryear', 'player', 'points', 'week', 'season', 'position']],
        left_on=['Name Full', 'Year'],
        right_on=['player', 'season'],
        how='left'
    )

    merged_data = merged_data[
        ((merged_data['Year'].astype(int) < 2021) & (merged_data['week'] <= 16)) |
        ((merged_data['Year'].astype(int) >= 2021) & (merged_data['week'] <= 17))
    ]

    if include_drafted and not include_keepers:
        merged_data = merged_data[merged_data['Is Keeper Status'] != 1]
    elif not include_drafted and include_keepers:
        merged_data = merged_data[merged_data['Is Keeper Status'] == 1]
    elif not include_drafted and not include_keepers:
        merged_data = pd.DataFrame()

    aggregated_data = merged_data.groupby(['season', 'player', 'position']).agg({
        'points': 'sum',
        'Cost': 'first',
        'Pick': 'first',
        'Name Full': 'first',
        'Team Manager': 'first',
        'week': pd.Series.nunique
    }).reset_index()

    aggregated_data['PPG'] = (aggregated_data['points'] / aggregated_data['week']).round(2)

    # Fixed Cost Rank logic
    def cost_rank_group(group):
        year = str(group['season'].iloc[0])
        if year in ['2014', '2015']:
            # Find the largest Pick for the entire year
            year_mask = aggregated_data['season'] == year
            max_pick_year = aggregated_data.loc[year_mask, 'Pick'].max()
            fill_value = max_pick_year + 1 if not pd.isna(max_pick_year) else 9999
            group['Pick_filled'] = group['Pick'].fillna(fill_value)
            return group['Pick_filled'].rank(method='first', ascending=True).astype(int)
        else:
            return group['Cost'].rank(method='first', ascending=False).astype(int)

    aggregated_data['Cost Rank'] = aggregated_data.groupby(['season', 'position'], group_keys=False).apply(
        cost_rank_group)

    aggregated_data['Total Points Rank'] = aggregated_data.groupby(['season', 'position'])['points'].rank(method='first', ascending=False).astype(int)
    aggregated_data['PPG Rank'] = aggregated_data.groupby(['season', 'position'])['PPG'].rank(method='first', ascending=False).astype(int)

    aggregated_data.rename(columns={
        'points': 'Total Points',
        'Name Full': 'Player',
        'week': 'Unique Weeks'
    }, inplace=True)
    aggregated_data = aggregated_data[aggregated_data['position'].isin(allowed_primary_positions)]

    if selected_primary_positions:
        aggregated_data = aggregated_data[aggregated_data['position'].isin(selected_primary_positions)]
    if search_players:
        aggregated_data = aggregated_data[aggregated_data['player'].isin(search_players)]

    position_order = {pos: i for i, pos in enumerate(allowed_primary_positions)}
    aggregated_data['position_order'] = aggregated_data['position'].map(position_order)

    columns_to_display = [
        'season', 'Player', 'position',
        'Cost Rank', 'Total Points Rank', 'PPG Rank',
        'Total Points', 'PPG', 'Cost', 'Team Manager'
    ]

    st.write("Ranks are shown in the context of the player's positon and year")
    st.dataframe(aggregated_data[columns_to_display], hide_index=True)