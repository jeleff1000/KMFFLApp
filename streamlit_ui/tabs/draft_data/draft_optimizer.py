import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value

# Set page configuration to hide the top viewer
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", menu_items={
    'Get Help': None,
    'Report a bug': None,
    'About': None
})

def display_draft_optimizer(draft_history, player_data):
    st.header("Draft Optimizer")

    # Ensure 'Year' and 'season' columns have the same data type
    draft_history['Year'] = draft_history['Year'].astype(int)
    player_data['season'] = player_data['season'].astype(int)

    # Ensure 'Cost' column is float
    draft_history['Cost'] = draft_history['Cost'].astype(float)

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

    # Input fields for number of players for each position
    st.subheader("Optimizer Inputs")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        start_year = st.number_input("Select Start Year", min_value=draft_history['Year'].min(), max_value=draft_history['Year'].max(), value=draft_history['Year'].min())
    with col2:
        end_year = st.number_input("Select End Year", min_value=draft_history['Year'].min(), max_value=draft_history['Year'].max(), value=draft_history['Year'].max())
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

    # Filter the draft history and player data based on the selected date range
    filtered_draft_history = draft_history[(draft_history['Year'] >= int(start_year)) & (draft_history['Year'] <= int(end_year))]
    filtered_player_data = player_data[(player_data['season'] >= int(start_year)) & (player_data['season'] <= int(end_year))]

    # Exclude players with 'Is Keeper Status' equal to 1
    filtered_draft_history = filtered_draft_history[filtered_draft_history['Is Keeper Status'] != 1]

    # Merge draft_history with player_data to get points and weeks
    merged_data = filtered_draft_history.merge(filtered_player_data[['playeryear', 'player', 'points', 'week', 'season']], left_on=['Name Full', 'Year'], right_on=['player', 'season'], how='left')

    # Filter merged data to only include weeks up to 16 if year is prior to 2021 and up to 17 if 2021 or later
    merged_data = merged_data[(merged_data['Year'] < 2021) & (merged_data['week'] <= 16) | (merged_data['Year'] >= 2021) & (merged_data['week'] <= 17)]

    # Aggregate data by 'Name Full' and 'Year'
    aggregated_data = merged_data.groupby(['Name Full', 'Year', 'Primary Position']).agg({
        'Cost': 'max',
        'points': 'sum',
        'week': pd.Series.nunique
    }).reset_index()

    # Calculate PPG (Points Per Game)
    aggregated_data['PPG'] = aggregated_data['points'] / aggregated_data['week']

    # Remove rows with invalid PPG values
    aggregated_data = aggregated_data.dropna(subset=['PPG'])
    aggregated_data = aggregated_data[aggregated_data['PPG'].apply(lambda x: x != float('inf'))]

    # Sort by 'Year', 'Primary Position', and 'Cost' in descending order
    aggregated_data = aggregated_data.sort_values(by=['Year', 'Primary Position', 'Cost'], ascending=[True, True, False])

    # Rank each position by 'Cost' for each 'Year'
    aggregated_data['Rank'] = aggregated_data.groupby(['Year', 'Primary Position'])['Cost'].rank(method='first', ascending=False).astype(int)

    # Create a column with position rank like RB1, RB2, etc.
    aggregated_data['Position Rank'] = aggregated_data['Primary Position'] + aggregated_data['Rank'].astype(str)

    # Calculate average PPG for each position rank within the date range
    avg_ppg_data = aggregated_data.groupby('Position Rank').agg({
        'PPG': 'mean',
        'Cost': 'mean',
        'points': 'sum'
    }).reset_index()
    avg_ppg_data.rename(columns={'PPG': 'Average PPG', 'Cost': 'Average Cost', 'points': 'Total Points'}, inplace=True)

    # Round values to two decimal places
    avg_ppg_data = avg_ppg_data.round(2)

    # Filter out players with average cost below 0.85
    avg_ppg_data = avg_ppg_data[avg_ppg_data['Average Cost'] >= 0.85]

    # Prepare data for linear programming
    costs = avg_ppg_data['Average Cost'].values
    ppgs = avg_ppg_data['Average PPG'].values

    # Define the linear programming problem
    prob = LpProblem("Draft_Optimizer", LpMaximize)

    # Define the decision variables
    x = [LpVariable(f"x{i}", cat="Binary") for i in range(len(costs))]

    # Objective function
    prob += lpSum([ppgs[i] * x[i] for i in range(len(ppgs))])

    # Budget constraint
    prob += lpSum([costs[i] * x[i] for i in range(len(costs))]) <= budget

    # Position constraints
    position_constraints = {
        'QB': num_qb,
        'RB': num_rb,
        'WR': num_wr,
        'TE': num_te,
        'DEF': num_def,
        'K': num_k
    }

    for position, num in position_constraints.items():
        if num > 0:
            position_mask = avg_ppg_data['Position Rank'].str.startswith(position).astype(int).tolist()
            prob += lpSum([position_mask[i] * x[i] for i in range(len(position_mask))]) == num

    # Solve the problem
    prob.solve()

    # Extract the optimal draft slots
    optimal_slots = [value(x[i]) for i in range(len(x))]

    # Convert optimal_slots to a boolean array
    optimal_slots = [bool(slot) for slot in optimal_slots]

    # Filter the avg_ppg_data to get the optimal draft slots
    optimal_draft = avg_ppg_data[optimal_slots]

    # Round values to two decimal places
    optimal_draft = optimal_draft.round(2)

    # Display the optimizer and summary side by side
    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(optimal_draft, hide_index=True)
    with col2:
        total_cost = optimal_draft['Average Cost'].sum().round(2)
        total_ppg = optimal_draft['Average PPG'].sum().round(2)
        st.markdown("### Summary")
        st.markdown(f"""
        <div style="border:1px solid #ddd; padding: 10px; border-radius: 5px;">
            <p><strong>Total Cost:</strong> ${total_cost}</p>
            <p><strong>Total Points Per Game:</strong> {total_ppg}</p>
        </div>
        """, unsafe_allow_html=True)

        # Ensure the total cost does not exceed the budget
        if total_cost > budget:
            st.error("The total cost exceeds the budget. Please adjust the inputs.")