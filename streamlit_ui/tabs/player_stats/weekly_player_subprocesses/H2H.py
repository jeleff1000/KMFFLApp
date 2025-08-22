import streamlit as st
import pandas as pd

class H2HViewer:
    def __init__(self, filtered_data, matchup_data):
        self.filtered_data = filtered_data
        self.matchup_data = matchup_data

        # Add position rank to the filtered_data
        self.add_position_rank()

        # Ensure 'Matchup Name' is created in matchup_data
        self.add_matchup_names()

    def add_position_rank(self):
        # Sort by owner, week, season, fantasy position, points (descending), and player (alphabetically)
        self.filtered_data = self.filtered_data.sort_values(
            by=['owner', 'week', 'season', 'fantasy position', 'points', 'player'],
            ascending=[True, True, True, True, False, True]
        )

        # Group by owner, week, season, and fantasy position, then rank players within each group
        self.filtered_data['position_rank'] = self.filtered_data.groupby(
            ['owner', 'week', 'season', 'fantasy position']
        ).cumcount() + 1

        # Concatenate the rank with the fantasy position
        self.filtered_data['fantasy position'] = self.filtered_data.apply(
            lambda row: f"{row['fantasy position']}{row['position_rank']}", axis=1
        )

    def add_matchup_names(self):
        # Ensure 'Matchup Name' is created
        if all(col in self.matchup_data.columns for col in ['Manager', 'opponent']):
            self.matchup_data['Team 1'] = self.matchup_data.apply(
                lambda row: min(row['Manager'], row['opponent']), axis=1
            )
            self.matchup_data['Team 2'] = self.matchup_data.apply(
                lambda row: max(row['Manager'], row['opponent']), axis=1
            )
            self.matchup_data['Matchup Name'] = self.matchup_data.apply(
                lambda row: f"{row['Team 1']} vs. {row['Team 2']}", axis=1
            )
        else:
            raise KeyError("Required columns 'Manager' and 'opponent' are missing in matchup_data.")

    def get_matchup_names(self):
        # Return the matchup names DataFrame
        return self.matchup_data[['Manager', 'week', 'year', 'Matchup Name']]

    def display(self, prefix):
        # Ensure 'season' and 'year' columns have the same data type
        self.filtered_data['season'] = self.filtered_data['season'].astype(int)
        self.matchup_data['year'] = self.matchup_data['year'].astype(int)

        # Merge player data with matchup data
        merged_data = pd.merge(
            self.filtered_data,
            self.matchup_data,
            left_on=['owner', 'week', 'season'],
            right_on=['Manager', 'week', 'year'],
            how='inner'
        )

        # Add 'started' column
        merged_data['started'] = ~merged_data['fantasy position'].isin(['BN', 'IR'])

        # Convert 'optimal_player' to boolean
        merged_data['optimal_player'] = merged_data['optimal_player'] == 1

        # Add Team 1, Team 2, and Matchup Name columns
        if 'Matchup Name' not in merged_data.columns:
            merged_data['Team 1'] = merged_data.apply(
                lambda row: min(row['Manager'], row['opponent']), axis=1
            )
            merged_data['Team 2'] = merged_data.apply(
                lambda row: max(row['Manager'], row['opponent']), axis=1
            )
            merged_data['Matchup Name'] = merged_data.apply(
                lambda row: f"{row['Team 1']} vs. {row['Team 2']}", axis=1
            )

        if 'win' in merged_data.columns:
            merged_data['win'] = merged_data['win'] == 1
            merged_data['is_playoffs_check'] = merged_data['is_playoffs'] == 1

            # Perform a self-merge to find opponent points and opponent player
            merged_data = merged_data.merge(
                merged_data[['Manager', 'week', 'fantasy position', 'player', 'points']],
                left_on=['opponent', 'week', 'fantasy position'],
                right_on=['Manager', 'week', 'fantasy position'],
                how='left',
                suffixes=('', '_opponent')
            )

            # Assign opponent points and opponent player
            merged_data['opponent_points'] = merged_data['points_opponent']
            merged_data['opponent_player'] = merged_data['player_opponent']

            # Drop intermediate columns
            merged_data.drop(columns=['points_opponent', 'player_opponent'], inplace=True)

            # Create display DataFrame with the required columns
            display_df = merged_data[
                ['Manager', 'player', 'points', 'fantasy position', 'opponent_points', 'opponent_player', 'opponent',
                 'Team 1', 'Team 2', 'Matchup Name']
            ].rename(columns={
                'fantasy position': 'position',
                'opponent_points': 'opponent points',
                'opponent_player': 'opponent player'
            })

            # Sort and reset index
            display_df = display_df.sort_values(by=['Manager', 'player']).reset_index(drop=True)

            # Display the DataFrame in Streamlit
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column 'win' is not available in the data.")

        # Display the entire unfiltered filtered_data DataFrame
        st.subheader("Full Filtered Data")
        st.dataframe(self.filtered_data, hide_index=True)

        # Display the entire unfiltered matchup_data DataFrame
        st.subheader("Full Matchup Data")
        st.dataframe(self.matchup_data, hide_index=True)