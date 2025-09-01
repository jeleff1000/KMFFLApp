import streamlit as st
import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value
from joblib import Parallel, delayed

@st.cache_data
def preprocess_data(draft_history, player_data, start_year, end_year):
    # Ensure 'Year' and 'season' columns have the same data type
    draft_history['Year'] = draft_history['Year'].astype(int)
    player_data['season'] = player_data['season'].astype(int)

    # Ensure 'Cost' column is float
    draft_history['Cost'] = draft_history['Cost'].astype(float)

    # Filter the draft history and player data based on the selected date range
    filtered_draft_history = draft_history[(draft_history['Year'] >= int(start_year)) & (draft_history['Year'] <= int(end_year)) & (draft_history['Cost'] > 0)]
    filtered_player_data = player_data[(player_data['season'] >= int(start_year)) & (player_data['season'] <= int(end_year))]

    # Exclude players with 'Is Keeper Status' equal to 1
    filtered_draft_history = filtered_draft_history[filtered_draft_history['Is Keeper Status'] != 1]

    # Merge draft_history with player_data to get points and weeks
    merged_data = filtered_draft_history.merge(filtered_player_data[['playeryear', 'player', 'points', 'week', 'season']], left_on=['Name Full', 'Year'], right_on=['player', 'season'], how='left')

    # Filter merged data to only include weeks up to 16 if year is prior to 2021 and up to 17 if 2021 or later
    merged_data = merged_data[(merged_data['Year'] < 2021) & (merged_data['week'] <= 16) | (merged_data['Year'] >= 2021) & (merged_data['week'] <= 17)]

    # Filter out games where points are 0
    merged_data = merged_data[merged_data['points'] > 0]

    # Aggregate data by 'Name Full' and 'Year'
    aggregated_data = merged_data.groupby(['Name Full', 'Year', 'Primary Position']).agg({
        'Cost': 'max',
        'points': 'sum',
        'week': 'nunique'
    }).reset_index()

    # Calculate PPG (Points Per Game)
    aggregated_data['PPG'] = aggregated_data['points'] / aggregated_data['week']

    # Remove rows with invalid PPG values
    aggregated_data = aggregated_data.dropna(subset=['PPG'])
    aggregated_data = aggregated_data[aggregated_data['PPG'].apply(lambda x: x != float('inf'))]

    # Filter aggregated_data to only include rows where Cost is greater than 0
    aggregated_data = aggregated_data[aggregated_data['Cost'] > 0]

    return aggregated_data

def apply_price_constraints(df, constraints, position, num_position):
    if num_position == 0:
        return df[df['Primary Position'] != position]
    for i, max_cost in enumerate(constraints):
        df = df[~((df['Primary Position'] == position) & (df['Cost'] > max_cost))]
    return df

def assign_cost_buckets(df):
    df = df.sort_values(by='Cost')
    df['Cost Bucket'] = (df.groupby(['Primary Position', 'Year']).cumcount() // 3) + 1
    return df

def display_draft_optimizer(draft_history, player_data):
    st.header("Draft Optimizer")

    # Check if required columns exist in player_data
    required_columns = ['playeryear', 'player', 'points', 'week', 'season']
    for col in required_columns:
        if col not in player_data.columns:
            st.error(f"Column '{col}' not found in player_data DataFrame")
            return

    # Check if 'Name Full', 'Primary Position', and 'Is Keeper Status' columns exist in draft_history
    required_draft_columns = ['Name Full', 'Primary Position', 'Is Keeper Status']
    for col in required_draft_columns:
        if col not in draft_history.columns:
            st.error(f"Column '{col}' not found in draft_history DataFrame")
            return

    # Filter draft_history to only include rows where Cost is greater than 0
    draft_history_with_cost = draft_history[draft_history['Cost'] > 0]

    st.subheader("Optimizer Inputs")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        start_year = st.number_input("Select Start Year", min_value=int(draft_history_with_cost['Year'].min()),
                                     max_value=int(draft_history_with_cost['Year'].max()),
                                     value=int(draft_history_with_cost['Year'].min()))
    with col2:
        end_year = st.number_input("Select End Year", min_value=int(draft_history_with_cost['Year'].min()),
                                   max_value=int(draft_history_with_cost['Year'].max()),
                                   value=int(draft_history_with_cost['Year'].max()))
    with col3:
        budget = st.number_input("Enter Budget", min_value=0, value=200)
    col4, col5, col6 = st.columns([1, 1, 1])
    with col4:
        num_qb = st.number_input("Number of QBs", min_value=0, value=1)
    with col5:
        num_def = st.number_input("Number of DEFs", min_value=0, value=1)
    with col6:
        num_k = st.number_input("Number of Ks", min_value=0, value=1)
    col7, col8, col9 = st.columns([1, 1, 1])
    with col7:
        num_rb = st.number_input("Number of RBs", min_value=0, value=2)
    with col8:
        num_wr = st.number_input("Number of WRs", min_value=0, value=3)
    with col9:
        num_te = st.number_input("Number of TEs", min_value=0, value=1)
    col10, = st.columns([1])
    with col10:
        num_flex = st.number_input("Number of FLEX (WR/RB/TE)", min_value=0, value=1)

    with st.expander("Set Price Constraints for All Positions"):
        qb_constraints = [
            st.number_input(f"Max Cost for QB {i + 1}", min_value=0, max_value=100, value=100, key=f"qb_{i + 1}") for i
            in range(num_qb)]
        def_constraints = [
            st.number_input(f"Max Cost for DEF {i + 1}", min_value=0, max_value=100, value=100, key=f"def_{i + 1}") for
            i in range(num_def)]
        k_constraints = [
            st.number_input(f"Max Cost for K {i + 1}", min_value=0, max_value=100, value=100, key=f"k_{i + 1}") for i in
            range(num_k)]
        rb_constraints = []
        for i in range(num_rb):
            if i == 0:
                rb_constraints.append(
                    st.number_input(f"Max Cost for RB {i + 1}", min_value=0, max_value=100, value=100,
                                    key=f"rb_{i + 1}"))
            else:
                rb_constraints.append(
                    st.number_input(f"Max Cost for RB {i + 1}", min_value=0, max_value=rb_constraints[i - 1],
                                    value=rb_constraints[i - 1], key=f"rb_{i + 1}"))
        wr_constraints = []
        for i in range(num_wr):
            if i == 0:
                wr_constraints.append(
                    st.number_input(f"Max Cost for WR {i + 1}", min_value=0, max_value=100, value=100,
                                    key=f"wr_{i + 1}"))
            else:
                wr_constraints.append(
                    st.number_input(f"Max Cost for WR {i + 1}", min_value=0, max_value=wr_constraints[i - 1],
                                    value=wr_constraints[i - 1], key=f"wr_{i + 1}"))
        te_constraints = []
        for i in range(num_te):
            if i == 0:
                te_constraints.append(
                    st.number_input(f"Max Cost for TE {i + 1}", min_value=0, max_value=100, value=100,
                                    key=f"te_{i + 1}"))
            else:
                te_constraints.append(
                    st.number_input(f"Max Cost for TE {i + 1}", min_value=0, max_value=te_constraints[i - 1],
                                    value=te_constraints[i - 1], key=f"te_{i + 1}"))
        flex_constraints = []
        for i in range(num_flex):
            flex_constraints.append(
                st.number_input(f"Max Cost for FLEX {i + 1}", min_value=0, max_value=100, value=100,
                                key=f"flex_{i + 1}"))
        # Add Max Bid number input
        max_bid = st.number_input("Max Bid (any player)", min_value=0, max_value=100, value=100, key="max_bid")

    if st.button("Optimize"):
        aggregated_data = preprocess_data(draft_history, player_data, start_year, end_year)

        # Apply Max Bid filter first
        aggregated_data = aggregated_data[aggregated_data['Cost'] <= max_bid]

        aggregated_data = apply_price_constraints(aggregated_data, qb_constraints, 'QB', num_qb)
        aggregated_data = apply_price_constraints(aggregated_data, def_constraints, 'DEF', num_def)
        aggregated_data = apply_price_constraints(aggregated_data, k_constraints, 'K', num_k)
        aggregated_data = apply_price_constraints(aggregated_data, rb_constraints, 'RB', num_rb)
        aggregated_data = apply_price_constraints(aggregated_data, wr_constraints, 'WR', num_wr)
        aggregated_data = apply_price_constraints(aggregated_data, te_constraints, 'TE', num_te)

        # FLEX: filter out WR/RB/TE above FLEX constraints
        for i, max_cost in enumerate(flex_constraints):
            aggregated_data = aggregated_data[~(
                    (aggregated_data['Primary Position'].isin(['WR', 'RB', 'TE'])) &
                    (aggregated_data['Cost'] > max_cost)
            )]

        aggregated_data = assign_cost_buckets(aggregated_data)

        avg_ppg_data = aggregated_data.groupby(['Primary Position', 'Cost Bucket']).agg({
            'PPG': 'median',
            'Cost': 'mean'
        }).reset_index()
        avg_ppg_data.columns = ['Primary Position', 'Cost Bucket', 'Median PPG', 'Average Cost']
        avg_ppg_data = avg_ppg_data.round(2)
        position_counts = aggregated_data.groupby(['Primary Position', 'Year']).size().reset_index(name='Count')
        avg_position_counts = position_counts.groupby('Primary Position')['Count'].mean().reset_index(
            name='Average Count')
        avg_ppg_data = avg_ppg_data.merge(avg_position_counts, on='Primary Position', how='left')
        avg_ppg_data = avg_ppg_data.drop(columns=['Cost Bucket', 'Average Count'])
        avg_ppg_data = avg_ppg_data[['Primary Position', 'Average Cost', 'Median PPG']]

        costs = avg_ppg_data['Average Cost'].values
        ppgs = avg_ppg_data['Median PPG'].values

        prob = LpProblem("Draft_Optimizer", LpMaximize)
        x = [LpVariable(f"x{i}", cat="Binary") for i in range(len(costs))]
        prob += lpSum([ppgs[i] * x[i] for i in range(len(ppgs))])
        prob += lpSum([costs[i] * x[i] for i in range(len(costs))]) <= budget

        position_constraints = {
            'QB': num_qb,
            'RB': num_rb,
            'WR': num_wr,
            'TE': num_te,
            'DEF': num_def,
            'K': num_k
        }
        # Enforce min and max for all positions
        for position, num in position_constraints.items():
            position_mask = avg_ppg_data['Primary Position'].str.startswith(position).astype(int).tolist()
            if position in ['WR', 'RB', 'TE']:
                prob += lpSum([position_mask[i] * x[i] for i in range(len(position_mask))]) >= num
                prob += lpSum([position_mask[i] * x[i] for i in range(len(position_mask))]) <= num + num_flex
            else:
                prob += lpSum([position_mask[i] * x[i] for i in range(len(position_mask))]) >= num
                prob += lpSum([position_mask[i] * x[i] for i in range(len(position_mask))]) <= num

        # FLEX constraint: total WR/RB/TE slots = regular + FLEX
        total_wr_rb_te = num_wr + num_rb + num_te + num_flex
        flex_mask = avg_ppg_data['Primary Position'].isin(['WR', 'RB', 'TE']).astype(int).tolist()
        prob += lpSum([flex_mask[i] * x[i] for i in range(len(flex_mask))]) == total_wr_rb_te

        prob.solve()
        optimal_slots = [value(x[i]) for i in range(len(x))]
        optimal_slots = [bool(slot) for slot in optimal_slots]
        optimal_draft = avg_ppg_data[optimal_slots]
        optimal_draft = optimal_draft.round(2)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(optimal_draft, hide_index=True)
        with col2:
            total_cost = optimal_draft['Average Cost'].sum().round(2)
            total_ppg = optimal_draft['Median PPG'].sum().round(2)
            st.markdown("### Summary")
            st.markdown(f"""
               <div style="border:1px solid #ddd; padding: 10px; border-radius: 5px;">
                   <p><strong>Total Cost:</strong> ${total_cost}</p>
                   <p><strong>Total Points Per Game:</strong> {total_ppg}</p>
               </div>
               """, unsafe_allow_html=True)
            if total_cost > budget:
                st.error("The total cost exceeds the budget. Please adjust the inputs.")