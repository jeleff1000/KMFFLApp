# UI_Tabs/Matchup_Data.py
import streamlit as st

class MatchupDataViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        st.header("Matchup Data")

        # Add checkboxes in a row with adjusted column widths
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            regular_season = st.checkbox("Regular Season", value=True)
        with col2:
            playoffs = st.checkbox("Playoffs")
        with col3:
            consolation = st.checkbox("Consolation")

        # Filter data based on checkboxes
        if self.df is not None:
            filtered_df = self.df.copy()
            if regular_season:
                filtered_df = filtered_df[(filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0)]
            if playoffs:
                filtered_df = filtered_df[filtered_df['is_playoffs'] == 1]
            if consolation:
                filtered_df = filtered_df[filtered_df['is_consolation'] == 1]

            # Add dropdowns for manager, opponent, and year with adjusted column widths
            col4, col5, col6 = st.columns([1, 1, 1])
            with col4:
                selected_managers = st.multiselect("Select Manager(s)", ["All"] + sorted(filtered_df['Manager'].unique().tolist()), default=["All"])
            with col5:
                selected_opponents = st.multiselect("Select Opponent(s)", ["All"] + sorted(filtered_df['opponent'].unique().tolist()), default=["All"])
            with col6:
                selected_years = st.multiselect("Select Year(s)", ["All"] + sorted(filtered_df['year'].astype(int).unique().tolist()), default=["All"])

            # Filter data based on dropdown selections
            if "All" not in selected_managers:
                filtered_df = filtered_df[filtered_df['Manager'].isin(selected_managers)]
            if "All" not in selected_opponents:
                filtered_df = filtered_df[filtered_df['opponent'].isin(selected_opponents)]
            if "All" not in selected_years:
                filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]

            # Check if 'team_points' and 'opponent_score' columns exist
            if 'team_points' in filtered_df.columns and 'opponent_score' in filtered_df.columns:
                # Display win-loss and score
                filtered_df['win_loss'] = filtered_df.apply(lambda row: 'Win' if row['team_points'] > row['opponent_score'] else 'Loss', axis=1)
                filtered_df = filtered_df[['Manager', 'opponent', 'year', 'team_points', 'opponent_score', 'win_loss']]
                # Ensure the year column is converted to the last two digits
                filtered_df['year'] = filtered_df['year'].astype(str).str[-2:].astype(int)
                # Ensure the index is reset and dropped before displaying the DataFrame
                filtered_df = filtered_df.reset_index(drop=True)
                st.dataframe(filtered_df)

                # Display summary data
                st.subheader("Summary Data")
                total_games = len(filtered_df)
                total_wins = len(filtered_df[filtered_df['win_loss'] == 'Win'])
                total_losses = len(filtered_df[filtered_df['win_loss'] == 'Loss'])
                avg_team_points = filtered_df['team_points'].mean()
                avg_opponent_points = filtered_df['opponent_score'].mean()

                st.write(f"Total Games: {total_games} | Total Wins: {total_wins} | Total Losses: {total_losses} | "
                         f"Avg Team Points: {avg_team_points:.2f} | Avg Opponent Points: {avg_opponent_points:.2f}")
            else:
                st.write("The required columns 'team_points' and 'opponent_score' are not available in the data.")
        else:
            st.write("No data available")