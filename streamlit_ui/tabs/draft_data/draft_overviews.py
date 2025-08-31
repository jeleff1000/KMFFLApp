import streamlit as st
import pandas as pd

def display_draft_overview(draft_data):
    st.header("Average Draft Prices")

    draft_data['Year'] = draft_data['Year'].astype(str)
    allowed_primary_positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
    position_order = pd.CategoricalDtype(allowed_primary_positions, ordered=True)

    if 'Primary Position' not in draft_data.columns:
        st.error("The 'Primary Position' column is missing from draft_data.")
        return

    years = sorted(draft_data['Year'].unique().tolist())
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox("Start Year", years, index=0, key="start_year_selectbox")
    with col2:
        end_year = st.selectbox("End Year", years, index=len(years)-1, key="end_year_selectbox")

    # Non-keeper filter (Is Keeper Status != 1)
    non_keeper_data = draft_data[
        (draft_data['Year'] >= start_year) &
        (draft_data['Year'] <= end_year) &
        (draft_data['Team Manager'].notnull()) &
        (draft_data['Team Manager'].str.strip() != "") &
        (draft_data['Primary Position'].isin(allowed_primary_positions)) &
        (draft_data['Cost'] > 0) &
        ((draft_data['Is Keeper Status'].isnull()) | (draft_data['Is Keeper Status'] != 1))
    ].copy()
    non_keeper_data['Primary Position'] = non_keeper_data['Primary Position'].astype(position_order)
    non_keeper_data['RankNum'] = (
        non_keeper_data.groupby(['Year', 'Primary Position'])['Cost']
        .rank(method='first', ascending=False)
        .astype(int)
    )
    agg_df = non_keeper_data.groupby(['Primary Position', 'RankNum']).agg(
        Avg_Cost=('Cost', 'mean'),
        Max_Cost=('Cost', 'max'),
        Min_Cost=('Cost', 'min'),
        Median_Cost=('Cost', 'median'),
        Times_Drafted=('Cost', 'count')
    ).reset_index()
    agg_df['Position Rank'] = agg_df['Primary Position'].astype(str) + agg_df['RankNum'].astype(str)
    agg_df['Primary Position'] = agg_df['Primary Position'].astype(position_order)
    agg_df = agg_df.sort_values(['Primary Position', 'RankNum'])
    agg_df = agg_df[agg_df['Times_Drafted'] >= 1]

    columns_to_display = [
        'Position Rank', 'Primary Position', 'Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'Times_Drafted'
    ]
    st.subheader("Average Drafted Player Prices")
    st.dataframe(agg_df[columns_to_display], hide_index=True)

    # Keeper filter (Is Keeper Status == 1)
    keeper_data = draft_data[
        (draft_data['Year'] >= start_year) &
        (draft_data['Year'] <= end_year) &
        (draft_data['Team Manager'].notnull()) &
        (draft_data['Team Manager'].str.strip() != "") &
        (draft_data['Primary Position'].isin(allowed_primary_positions)) &
        (draft_data['Cost'] > 0) &
        (draft_data['Is Keeper Status'] == 1)
    ].copy()
    keeper_data['Primary Position'] = keeper_data['Primary Position'].astype(position_order)
    keeper_data['RankNum'] = (
        keeper_data.groupby(['Year', 'Primary Position'])['Cost']
        .rank(method='first', ascending=False)
        .astype(int)
    )
    keeper_agg_df = keeper_data.groupby(['Primary Position', 'RankNum']).agg(
        Avg_Cost=('Cost', 'mean'),
        Max_Cost=('Cost', 'max'),
        Min_Cost=('Cost', 'min'),
        Median_Cost=('Cost', 'median'),
        Times_Drafted=('Cost', 'count')
    ).reset_index()
    keeper_agg_df['Position Rank'] = keeper_agg_df['Primary Position'].astype(str) + keeper_agg_df['RankNum'].astype(str)
    keeper_agg_df['Primary Position'] = keeper_agg_df['Primary Position'].astype(position_order)
    keeper_agg_df = keeper_agg_df.sort_values(['Primary Position', 'RankNum'])
    keeper_agg_df = keeper_agg_df[keeper_agg_df['Times_Drafted'] >= 1]

    st.subheader("Average Keeper Prices")
    st.dataframe(keeper_agg_df[columns_to_display], hide_index=True)