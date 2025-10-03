import streamlit as st
import pandas as pd

def display_scoring_outcomes(draft_data, player_df):
    st.header("Scoring Outcomes")

    draft_data['year'] = draft_data['year'].astype(str)
    draft_data['manager'] = draft_data['manager'].astype(str)
    player_df['year'] = player_df['year'].astype(str)

    if 'yahoo_position' not in player_df.columns:
        st.error("The 'yahoo_position' column is missing from player_df.")
        return

    years = sorted(draft_data['year'].unique().tolist())
    team_managers = sorted(draft_data['manager'].unique().tolist())
    allowed_primary_positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
    primary_positions = [
        pos for pos in sorted(
            [p for p in player_df['yahoo_position'].unique().tolist() if pd.notna(p)]
        ) if pos in allowed_primary_positions
    ]

    col1, col2 = st.columns([1, 1])
    with col1:
        search_players = st.multiselect("Search Player", options=player_df['player'].unique().tolist(), default=[])
    with col2:
        selected_team_managers = st.multiselect("Select manager", team_managers, default=[])

    col3, col4 = st.columns([1, 1])
    with col3:
        selected_years = st.multiselect("Select year", years, default=[])
    with col4:
        selected_primary_positions = st.multiselect("Select Primary Position", primary_positions, default=[])

    col5, col6 = st.columns([1, 1])
    with col5:
        include_drafted = st.checkbox("Include Drafted", value=True, key="include_drafted")
    with col6:
        include_keepers = st.checkbox("Include Keepers", value=True, key="include_keepers")

    if selected_years:
        draft_data = draft_data[draft_data['year'].isin(selected_years)]
        player_df = player_df[player_df['year'].isin(selected_years)]
    if selected_team_managers:
        draft_data = draft_data[draft_data['manager'].isin(selected_team_managers)]

    merged_data = draft_data.merge(
        player_df[['player', 'points', 'week', 'year', 'yahoo_position']],
        left_on=['player_name', 'year'],
        right_on=['player', 'year'],
        how='left'
    )

    merged_data = merged_data[
        ((merged_data['year'].astype(int) < 2021) & (merged_data['week'] <= 16)) |
        ((merged_data['year'].astype(int) >= 2021) & (merged_data['week'] <= 17))
    ]

    if include_drafted and not include_keepers:
        merged_data = merged_data[merged_data['is_keeper_status'] != 1]
    elif not include_drafted and include_keepers:
        merged_data = merged_data[merged_data['is_keeper_status'] == 1]
    elif not include_drafted and not include_keepers:
        merged_data = pd.DataFrame()

    if merged_data.empty:
        st.write("No data to display after filtering.")
        return

    merged_data['position'] = merged_data['primary_position']

    aggregated_data = merged_data.groupby(['year', 'player', 'position']).agg({
        'points': 'sum',
        'cost': 'first',
        'pick': 'first',
        'manager': 'first',
        'week': pd.Series.nunique
    }).reset_index()

    aggregated_data['ppg'] = (aggregated_data['points'] / aggregated_data['week']).round(2)

    def cost_rank_logic(row, group):
        year = str(row['year'])
        if year in ['2014', '2015']:
            max_pick = group['pick'].max()
            fill_value = max_pick + 1 if not pd.isna(max_pick) else 9999
            pick_filled = group['pick'].fillna(fill_value)
            return pick_filled.rank(method='first', ascending=True)[row.name]
        else:
            return group['cost'].rank(method='first', ascending=False)[row.name]

    def cost_rank_transform(df):
        result = pd.Series(index=df.index, dtype=int)
        for (year, position), group in df.groupby(['year', 'position']):
            for idx in group.index:
                result[idx] = cost_rank_logic(df.loc[idx], group)
        return result

    aggregated_data['cost_rank'] = cost_rank_transform(aggregated_data)
    aggregated_data['total_points_rank'] = aggregated_data.groupby(['year', 'position'])['points'].transform(
        lambda x: x.rank(method='first', ascending=False).astype(int)
    )
    aggregated_data['ppg_rank'] = aggregated_data.groupby(['year', 'position'])['ppg'].transform(
        lambda x: x.rank(method='first', ascending=False).astype(int)
    )

    aggregated_data.rename(columns={
        'points': 'total_points',
        'player': 'Player',
        'week': 'unique_weeks',
        'cost_rank': 'Cost Rank',
        'total_points_rank': 'Total Points Rank',
        'ppg_rank': 'PPG Rank',
        'total_points': 'Total Points',
        'ppg': 'PPG',
        'cost': 'Cost',
        'manager': 'manager'
    }, inplace=True)

    aggregated_data = aggregated_data[aggregated_data['position'].isin(allowed_primary_positions)]

    if selected_primary_positions:
        aggregated_data = aggregated_data[aggregated_data['position'].isin(selected_primary_positions)]
    if search_players:
        aggregated_data = aggregated_data[aggregated_data['Player'].isin(search_players)]

    position_order = {pos: i for i, pos in enumerate(allowed_primary_positions)}
    aggregated_data['position_order'] = aggregated_data['position'].map(position_order)

    columns_to_display = [
        'year', 'Player', 'position',
        'Cost Rank', 'Total Points Rank', 'PPG Rank',
        'Total Points', 'PPG', 'Cost', 'manager'
    ]
    columns_present = [col for col in columns_to_display if col in aggregated_data.columns]

    st.write("Ranks are shown in the context of the player's position and year")
    st.dataframe(aggregated_data[columns_present], hide_index=True)