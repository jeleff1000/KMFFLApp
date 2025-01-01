import streamlit as st
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from .shuffle_scores_and_schedules.shuffle_schedule import shuffle_schedule

@st.cache_data
def calculate_records(df, num_weeks):
    agg_df = df.groupby('Manager').agg({
        'Sim_Wins': 'sum'
    }).rename(columns={'Sim_Wins': 'Total_Wins'})

    agg_df['Sim_Record'] = agg_df['Total_Wins'].apply(lambda x: f"{int(x)}-{num_weeks-int(x)}")
    df = df.merge(agg_df[['Sim_Record']], left_on='Manager', right_index=True, how='left')

    return df

def perform_shuffle_and_record(filtered_df, num_weeks):
    shuffled_df = shuffle_schedule(filtered_df.copy())
    shuffled_df = calculate_records(shuffled_df, num_weeks)
    return shuffled_df

class ExpectedRecordViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        st.subheader("Expected Record Simulation")

        if self.df is not None:
            years = ["Select Year"] + sorted(self.df['year'].unique().tolist())
            col1, col2 = st.columns([1, 3])
            with col1:
                selected_year = st.selectbox("Select Year", years)

            if selected_year != "Select Year":
                filtered_df = self.df[(self.df['year'] == selected_year) &
                                      (self.df['is_playoffs'] == 0) &
                                      (self.df['is_consolation'] == 0)]
                num_weeks = filtered_df['week'].max()
                record_counts = {manager: {f"{wins}-{num_weeks-wins}": 0 for wins in range(num_weeks + 1)}
                                 for manager in filtered_df['Manager'].unique()}

                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(perform_shuffle_and_record, filtered_df, num_weeks) for _ in range(105)]
                    for future in futures:
                        shuffled_df = future.result()
                        for manager in shuffled_df['Manager'].unique():
                            sim_record = shuffled_df[shuffled_df['Manager'] == manager]['Sim_Record'].values[0]
                            record_counts[manager][sim_record] += 1

                record_percentages = {manager: {record: float(count) / 105 * 100
                                                for record, count in records.items()}
                                      for manager, records in record_counts.items()}

                results_df = pd.DataFrame(record_percentages).fillna(0).T

                # Sort columns from largest to smallest record
                results_df = results_df[sorted(results_df.columns, key=lambda x: int(x.split('-')[0]), reverse=True)]

                # Apply color scale only to record columns
                styled_results_df = results_df.style.background_gradient(
                    cmap='RdYlGn', axis=1
                )
                styled_results_df = styled_results_df.format("{:.2f}%")

                # Apply custom CSS to make the font smaller
                st.markdown(
                    """
                    <style>
                    .dataframe tbody tr td {
                        font-size: 8px;
                    }
                    </style>
                    """, unsafe_allow_html=True
                )

                st.dataframe(styled_results_df)
        else:
            st.write("No data available")