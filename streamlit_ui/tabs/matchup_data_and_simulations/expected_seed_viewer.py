import streamlit as st
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from .shuffle_scores_and_schedules.shuffle_schedule import shuffle_schedule
from .matchups.weekly_matchup_overview import WeeklyMatchupDataViewer  # Add this import

@st.cache_data
def calculate_playoff_seed(df):
    agg_df = df.groupby('Manager').agg({
        'Sim_Wins': 'sum',
        'team_points': 'sum'
    }).rename(columns={'Sim_Wins': 'Sim_Wins', 'team_points': 'Total_Tweaked_Points'})

    agg_df = agg_df.sort_values(by=['Sim_Wins', 'Total_Tweaked_Points'], ascending=[False, False])
    agg_df['Sim_Playoff_Seed'] = range(1, len(agg_df) + 1)
    df = df.merge(agg_df[['Sim_Playoff_Seed']], left_on='Manager', right_index=True, how='left')

    return df

def perform_shuffle_and_seed(filtered_df):
    shuffled_df = shuffle_schedule(filtered_df.copy())
    shuffled_df = calculate_playoff_seed(shuffled_df)
    return shuffled_df

class ExpectedSeedViewer(WeeklyMatchupDataViewer):
    def __init__(self, matchup_data_df, player_data_df):
        super().__init__(matchup_data_df, player_data_df)
        self.df = matchup_data_df

    def display(self):
        st.subheader("Expected Seed Simulation")

        if self.df is not None:
            years = ["Select Year"] + sorted(self.df['year'].unique().tolist())
            col1, col2 = st.columns([1, 3])
            with col1:
                selected_year = st.selectbox("Select Year", years)

            if selected_year != "Select Year":
                filtered_df = self.df[(self.df['year'] == selected_year) &
                                      (self.df['is_playoffs'] == 0) &
                                      (self.df['is_consolation'] == 0)]
                seed_counts = {manager: {seed: 0 for seed in range(1, len(filtered_df['Manager'].unique()) + 1)}
                               for manager in filtered_df['Manager'].unique()}

                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(perform_shuffle_and_seed, filtered_df) for _ in range(105)]
                    for future in futures:
                        shuffled_df = future.result()
                        for manager in shuffled_df['Manager'].unique():
                            sim_seed = shuffled_df[shuffled_df['Manager'] == manager]['Sim_Playoff_Seed'].values[0]
                            seed_counts[manager][sim_seed] += 1

                seed_percentages = {manager: {seed: float(count) / 105 * 100
                                              for seed, count in seeds.items()}
                                    for manager, seeds in seed_counts.items()}

                results_df = pd.DataFrame(seed_percentages).fillna(0).T

                # Calculate Bye Week and Playoffs columns
                results_df['Bye Week'] = results_df.iloc[:, :2].sum(axis=1)
                results_df['Playoffs'] = results_df.iloc[:, :6].sum(axis=1)

                # Apply color scale only to seed columns
                seed_columns = results_df.columns[:-2]
                styled_results_df = results_df.style.background_gradient(
                    subset=seed_columns, cmap='RdYlGn', axis=1
                )
                styled_results_df = styled_results_df.format("{:.2f}%", subset=seed_columns)

                # Format Bye Week and Playoffs columns to have two decimal places
                styled_results_df = styled_results_df.format("{:.2f}%", subset=['Bye Week', 'Playoffs'])

                # Apply custom CSS to make the font smaller
                st.markdown(
                    """
                    <style>
                    .dataframe tbody tr td {
                        font-size: 10px;
                    }
                    </style>
                    """, unsafe_allow_html=True
                )

                st.dataframe(styled_results_df)
        else:
            st.write("No data available")