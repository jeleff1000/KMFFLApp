import streamlit as st
import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value


@st.cache_data
def preprocess_data(draft_history, player_data, start_year, end_year):
    """
    Optimized preprocessing with vectorized operations.
    Now uses pre-calculated cost_bucket from the data.
    """
    # Create copies to avoid modifying original data
    draft_history = draft_history.copy()
    player_data = player_data.copy()

    # Convert types once upfront (more efficient than multiple conversions)
    draft_history['year'] = pd.to_numeric(draft_history['year'], errors='coerce').astype('Int64')
    draft_history['cost'] = pd.to_numeric(draft_history['cost'], errors='coerce')
    draft_history['cost_bucket'] = pd.to_numeric(draft_history['cost_bucket'], errors='coerce').astype('Int64')

    player_data['year'] = pd.to_numeric(player_data['year'], errors='coerce').astype('Int64')
    player_data['points'] = pd.to_numeric(player_data['points'], errors='coerce')
    player_data['week'] = pd.to_numeric(player_data['week'], errors='coerce')

    # Single combined filter operation for draft history
    draft_mask = (
            (draft_history['year'] >= start_year) &
            (draft_history['year'] <= end_year) &
            (draft_history['cost'] > 0) &
            (draft_history['is_keeper_status'] != '1') &
            (draft_history['is_keeper_status'] != 1)  # Handle both string and int
    )
    filtered_draft = draft_history[draft_mask]

    # Single filter for player data
    player_mask = (
            (player_data['year'] >= start_year) &
            (player_data['year'] <= end_year) &
            (player_data['points'] > 0)  # Filter out 0 points here
    )
    filtered_player = player_data[player_mask]

    # Merge once with only needed columns
    merged = filtered_draft.merge(
        filtered_player[['player', 'points', 'week', 'year']],
        left_on=['player_name', 'year'],
        right_on=['player', 'year'],
        how='left'
    )

    # Vectorized week filtering based on year (regular season only)
    week_mask = (
            ((merged['year'] < 2021) & (merged['week'] <= 16)) |
            ((merged['year'] >= 2021) & (merged['week'] <= 17))
    )
    merged = merged[week_mask]

    # Single aggregation operation with cost_bucket included
    agg_data = merged.groupby(
        ['player_name', 'year', 'primary_position', 'cost_bucket'],
        dropna=False
    ).agg({
        'cost': 'max',
        'points': 'sum',
        'week': 'nunique'
    }).reset_index()

    # Vectorized PPG calculation
    agg_data['PPG'] = agg_data['points'] / agg_data['week']

    # Single cleanup operation - remove invalid PPG values
    valid_mask = (
            agg_data['PPG'].notna() &
            np.isfinite(agg_data['PPG']) &
            (agg_data['PPG'] > 0) &
            (agg_data['cost'] > 0)
    )

    return agg_data[valid_mask]


def apply_price_constraints_vectorized(df, position_constraints):
    """
    Apply all price constraints in a single vectorized operation.
    Much faster than iterating through each constraint separately.
    """
    mask = pd.Series(True, index=df.index)

    for position, constraints in position_constraints.items():
        if not constraints or len(constraints) == 0:
            continue

        # Create mask for this position
        pos_mask = df['primary_position'] == position

        # For each constraint, exclude players above that cost
        for max_cost in constraints:
            mask &= ~(pos_mask & (df['cost'] > max_cost))

    return df[mask]


def calculate_aggregated_buckets(aggregated_data):
    """
    Calculate median PPG and mean cost per position/bucket.
    Uses the pre-calculated cost_bucket column.
    """
    # Group by position and cost bucket (which is already calculated)
    result = aggregated_data.groupby(
        ['primary_position', 'cost_bucket'],
        dropna=False
    ).agg({
        'PPG': 'median',
        'cost': 'mean'
    }).reset_index()

    result.columns = ['primary_position', 'cost_bucket', 'Median PPG', 'Average cost']
    return result.round(2)


def display_draft_optimizer(draft_history, player_data):
    st.header("Draft Optimizer")

    # Validate required columns
    required_player_cols = ['player', 'points', 'week', 'year']
    required_draft_cols = ['player_name', 'primary_position', 'is_keeper_status', 'cost_bucket']

    missing_player = [col for col in required_player_cols if col not in player_data.columns]
    missing_draft = [col for col in required_draft_cols if col not in draft_history.columns]

    if missing_player:
        st.error(f"Missing columns in player_data: {', '.join(missing_player)}")
        return

    if missing_draft:
        st.error(f"Missing columns in draft_history: {', '.join(missing_draft)}")
        st.info("Make sure you've regenerated your data files with the updated merge_data.py script.")
        return

    # Filter for rows with cost > 0
    draft_history_with_cost = draft_history[pd.to_numeric(draft_history['cost'], errors='coerce') > 0].copy()

    if len(draft_history_with_cost) == 0:
        st.error("No draft data with cost > 0 found.")
        return

    # Get year range
    min_year = int(draft_history_with_cost['year'].min())
    max_year = int(draft_history_with_cost['year'].max())

    st.subheader("Optimizer Inputs")

    # Year and budget inputs
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        start_year = st.number_input(
            "Select Start Year",
            min_value=min_year,
            max_value=max_year,
            value=min_year
        )
    with col2:
        end_year = st.number_input(
            "Select End Year",
            min_value=min_year,
            max_value=max_year,
            value=max_year
        )
    with col3:
        budget = st.number_input("Enter Budget", min_value=0, value=200)

    # Position quantity inputs
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

    # Price constraints section
    with st.expander("Set Price Constraints for All Positions"):
        st.caption("Set maximum costs for each roster slot. Leave at 100 for no constraint.")

        # QB constraints
        qb_constraints = [
            st.number_input(f"Max cost for QB {i + 1}", min_value=0, max_value=100, value=100, key=f"qb_{i + 1}")
            for i in range(num_qb)
        ]

        # DEF constraints
        def_constraints = [
            st.number_input(f"Max cost for DEF {i + 1}", min_value=0, max_value=100, value=100, key=f"def_{i + 1}")
            for i in range(num_def)
        ]

        # K constraints
        k_constraints = [
            st.number_input(f"Max cost for K {i + 1}", min_value=0, max_value=100, value=100, key=f"k_{i + 1}")
            for i in range(num_k)
        ]

        # RB constraints (cascading max values)
        rb_constraints = []
        for i in range(num_rb):
            max_val = rb_constraints[i - 1] if i > 0 else 100
            rb_constraints.append(
                st.number_input(f"Max cost for RB {i + 1}", min_value=0, max_value=max_val, value=max_val,
                                key=f"rb_{i + 1}")
            )

        # WR constraints (cascading max values)
        wr_constraints = []
        for i in range(num_wr):
            max_val = wr_constraints[i - 1] if i > 0 else 100
            wr_constraints.append(
                st.number_input(f"Max cost for WR {i + 1}", min_value=0, max_value=max_val, value=max_val,
                                key=f"wr_{i + 1}")
            )

        # TE constraints (cascading max values)
        te_constraints = []
        for i in range(num_te):
            max_val = te_constraints[i - 1] if i > 0 else 100
            te_constraints.append(
                st.number_input(f"Max cost for TE {i + 1}", min_value=0, max_value=max_val, value=max_val,
                                key=f"te_{i + 1}")
            )

        # FLEX constraints
        flex_constraints = [
            st.number_input(f"Max cost for FLEX {i + 1}", min_value=0, max_value=100, value=100, key=f"flex_{i + 1}")
            for i in range(num_flex)
        ]

        # Global max bid
        max_bid = st.number_input("Max Bid (any player)", min_value=0, max_value=100, value=100, key="max_bid")

    # Optimize button
    if st.button("Optimize", type="primary"):
        with st.spinner("Processing data and optimizing lineup..."):
            try:
                # Preprocess data (cached for performance)
                aggregated_data = preprocess_data(draft_history, player_data, start_year, end_year)

                if len(aggregated_data) == 0:
                    st.error("No data available after filtering. Try adjusting your year range.")
                    return

                # Apply max bid filter
                aggregated_data = aggregated_data[aggregated_data['cost'] <= max_bid]

                # Build position constraints dictionary
                position_constraints = {
                    'QB': qb_constraints,
                    'DEF': def_constraints,
                    'K': k_constraints,
                    'RB': rb_constraints,
                    'WR': wr_constraints,
                    'TE': te_constraints
                }

                # Apply all position constraints at once (vectorized)
                aggregated_data = apply_price_constraints_vectorized(aggregated_data, position_constraints)

                # Apply FLEX constraints
                flex_mask = aggregated_data['primary_position'].isin(['WR', 'RB', 'TE'])
                for max_cost in flex_constraints:
                    aggregated_data = aggregated_data[~(flex_mask & (aggregated_data['cost'] > max_cost))]

                if len(aggregated_data) == 0:
                    st.error("No players available after applying constraints. Try relaxing your constraints.")
                    return

                # Calculate bucket aggregates (uses pre-calculated cost_bucket)
                avg_ppg_data = calculate_aggregated_buckets(aggregated_data)

                # Prepare data for optimization
                display_data = avg_ppg_data[['primary_position', 'Average cost', 'Median PPG']].copy()

                costs = display_data['Average cost'].values
                ppgs = display_data['Median PPG'].values

                # Set up linear programming problem
                prob = LpProblem("Draft_Optimizer", LpMaximize)
                x = [LpVariable(f"x{i}", cat="Binary") for i in range(len(costs))]

                # Objective: maximize total PPG
                prob += lpSum([ppgs[i] * x[i] for i in range(len(ppgs))])

                # Budget constraint
                prob += lpSum([costs[i] * x[i] for i in range(len(costs))]) <= budget

                # Position-specific constraints
                position_counts = {
                    'QB': num_qb,
                    'RB': num_rb,
                    'WR': num_wr,
                    'TE': num_te,
                    'DEF': num_def,
                    'K': num_k
                }

                for position, num in position_counts.items():
                    pos_mask = display_data['primary_position'].str.startswith(position).astype(int).tolist()

                    if position in ['WR', 'RB', 'TE']:
                        # Flex-eligible positions: min = num, max = num + flex slots
                        prob += lpSum([pos_mask[i] * x[i] for i in range(len(pos_mask))]) >= num
                        prob += lpSum([pos_mask[i] * x[i] for i in range(len(pos_mask))]) <= num + num_flex
                    else:
                        # Non-flex positions: exactly num players
                        prob += lpSum([pos_mask[i] * x[i] for i in range(len(pos_mask))]) >= num
                        prob += lpSum([pos_mask[i] * x[i] for i in range(len(pos_mask))]) <= num

                # FLEX total constraint: total WR/RB/TE must equal regular slots + FLEX slots
                total_wr_rb_te = num_wr + num_rb + num_te + num_flex
                flex_mask_list = display_data['primary_position'].isin(['WR', 'RB', 'TE']).astype(int).tolist()
                prob += lpSum([flex_mask_list[i] * x[i] for i in range(len(flex_mask_list))]) == total_wr_rb_te

                # Solve the optimization problem
                prob.solve()

                # Extract results
                optimal_slots = [bool(value(x[i])) for i in range(len(x))]
                optimal_draft = display_data[optimal_slots].copy().round(2)

                # Sort by position for better readability
                position_order = ['QB', 'RB', 'WR', 'TE', 'DEF', 'K']
                optimal_draft['sort_key'] = optimal_draft['primary_position'].apply(
                    lambda pos: position_order.index(pos) if pos in position_order else 999
                )
                optimal_draft = optimal_draft.sort_values(['sort_key', 'Average cost'], ascending=[True, False])
                optimal_draft = optimal_draft.drop(columns=['sort_key'])

                # Display results
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("Optimal Lineup")
                    st.dataframe(optimal_draft, hide_index=True, use_container_width=True)

                with col2:
                    total_cost = optimal_draft['Average cost'].sum().round(2)
                    total_ppg = optimal_draft['Median PPG'].sum().round(2)
                    remaining_budget = (budget - total_cost).round(2)

                    st.subheader("Summary")
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
                        <p style="margin: 5px 0;"><strong>Total Cost:</strong> ${total_cost}</p>
                        <p style="margin: 5px 0;"><strong>Remaining Budget:</strong> ${remaining_budget}</p>
                        <p style="margin: 5px 0;"><strong>Total PPG:</strong> {total_ppg}</p>
                        <p style="margin: 5px 0;"><strong>Players:</strong> {len(optimal_draft)}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if total_cost > budget:
                        st.error("⚠️ Total cost exceeds budget. Please adjust constraints.")
                    elif remaining_budget > 20:
                        st.warning(
                            f"💡 You have ${remaining_budget} left. Consider relaxing constraints to use more budget.")
                    else:
                        st.success("✅ Optimized lineup within budget!")

                # Position breakdown
                st.subheader("Position Breakdown")
                position_summary = optimal_draft.groupby('primary_position').agg({
                    'Average cost': ['sum', 'mean'],
                    'Median PPG': ['sum', 'mean'],
                    'primary_position': 'count'
                }).round(2)
                position_summary.columns = ['Total Cost', 'Avg Cost', 'Total PPG', 'Avg PPG', 'Count']
                st.dataframe(position_summary, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred during optimization: {str(e)}")
                st.exception(e)