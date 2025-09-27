import streamlit as st
import pandas as pd

def display_draft_overview(draft_data):
    st.header("Average Draft Prices")

    # Standardize column names to snake_case
    draft_data = draft_data.rename(columns={
        'Year': 'year',
        'Team Manager': 'manager',
        'Primary Position': 'primary_position',
        'Cost': 'cost',
        'Is Keeper Status': 'is_keeper_status'
    })

    draft_data['year'] = draft_data['year'].astype(str)
    allowed_primary_positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
    position_order = pd.CategoricalDtype(allowed_primary_positions, ordered=True)

    if 'primary_position' not in draft_data.columns:
        st.error("The 'primary_position' column is missing from draft_data.")
        return

    years = sorted(draft_data['year'].unique().tolist())
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox("Start Year", years, index=0, key="start_year_selectbox")
    with col2:
        end_year = st.selectbox("End Year", years, index=len(years)-1, key="end_year_selectbox")

    # Non-keeper filter (is_keeper_status != 1)
    non_keeper_data = draft_data[
        (draft_data['year'] >= start_year) &
        (draft_data['year'] <= end_year) &
        (draft_data['manager'].notnull()) &
        (draft_data['manager'].str.strip() != "") &
        (draft_data['primary_position'].isin(allowed_primary_positions)) &
        (draft_data['cost'] > 0) &
        ((draft_data['is_keeper_status'].isnull()) | (draft_data['is_keeper_status'] != 1))
    ].copy()
    non_keeper_data['primary_position'] = non_keeper_data['primary_position'].astype(position_order)
    non_keeper_data['rank_num'] = (
        non_keeper_data.groupby(['year', 'primary_position'])['cost']
        .rank(method='first', ascending=False)
        .astype(int)
    )
    agg_df = non_keeper_data.groupby(['primary_position', 'rank_num']).agg(
        avg_cost=('cost', 'mean'),
        max_cost=('cost', 'max'),
        min_cost=('cost', 'min'),
        median_cost=('cost', 'median'),
        times_drafted=('cost', 'count')
    ).reset_index()
    agg_df['position_rank'] = agg_df['primary_position'].astype(str) + agg_df['rank_num'].astype(str)
    agg_df['primary_position'] = agg_df['primary_position'].astype(position_order)
    agg_df = agg_df.sort_values(['primary_position', 'rank_num'])
    agg_df = agg_df[agg_df['times_drafted'] >= 1]

    columns_to_display = [
        'position_rank', 'primary_position', 'avg_cost', 'max_cost', 'min_cost', 'median_cost', 'times_drafted'
    ]
    st.subheader("Average Drafted Player Prices")
    st.dataframe(agg_df[columns_to_display], hide_index=True)

    # Keeper filter (is_keeper_status == 1)
    keeper_data = draft_data[
        (draft_data['year'] >= start_year) &
        (draft_data['year'] <= end_year) &
        (draft_data['manager'].notnull()) &
        (draft_data['manager'].str.strip() != "") &
        (draft_data['primary_position'].isin(allowed_primary_positions)) &
        (draft_data['cost'] > 0) &
        (draft_data['is_keeper_status'] == 1)
    ].copy()
    keeper_data['primary_position'] = keeper_data['primary_position'].astype(position_order)
    keeper_data['rank_num'] = (
        keeper_data.groupby(['year', 'primary_position'])['cost']
        .rank(method='first', ascending=False)
        .astype(int)
    )
    keeper_agg_df = keeper_data.groupby(['primary_position', 'rank_num']).agg(
        avg_cost=('cost', 'mean'),
        max_cost=('cost', 'max'),
        min_cost=('cost', 'min'),
        median_cost=('cost', 'median'),
        times_drafted=('cost', 'count')
    ).reset_index()
    keeper_agg_df['position_rank'] = keeper_agg_df['primary_position'].astype(str) + keeper_agg_df['rank_num'].astype(str)
    keeper_agg_df['primary_position'] = keeper_agg_df['primary_position'].astype(position_order)
    keeper_agg_df = keeper_agg_df.sort_values(['primary_position', 'rank_num'])
    keeper_agg_df = keeper_agg_df[keeper_agg_df['times_drafted'] >= 1]

    st.subheader("Average Keeper Prices")
    st.dataframe(keeper_agg_df[columns_to_display], hide_index=True)