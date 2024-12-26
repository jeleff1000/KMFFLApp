# Simulations_Streamlit.py
import streamlit as st
import pandas as pd
import pickle

# Function to load the pickle file
def load_pickle_file(uploaded_file):
    try:
        df_dict = pickle.load(uploaded_file)
        return df_dict
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None

# Function to calculate Gavi Stat
def calculate_gavi_stat(df, selected_year, include_playoffs, opponent=False):
    if selected_year != "All Years":
        df = df[df['year'] == int(selected_year)]

    df = df[df['is_consolation'] != 1]
    if not include_playoffs:
        df = df[df['is_playoffs'] != 1]

    df['teams_beat_this_week'] = df['teams_beat_this_week'].fillna(0)

    if opponent:
        gavi_stat_df = df.groupby('opponent').agg(
            win=('win', 'sum'),
            loss=('win', 'count'),
            teams_beat_this_week=('teams_beat_this_week', 'sum')
        ).reset_index()
        gavi_stat_df.rename(columns={'opponent': 'Manager'}, inplace=True)
        gavi_stat_df['loss'] = gavi_stat_df['loss'] - gavi_stat_df['win']
        gavi_stat_df['record'] = gavi_stat_df['loss'].astype(str) + " - " + gavi_stat_df['win'].astype(str)
        gavi_stat_df['expected_wins'] = (gavi_stat_df['teams_beat_this_week'] / 9).round(2)
        gavi_stat_df['expected_record'] = (gavi_stat_df['win'] + gavi_stat_df['loss'] - gavi_stat_df['expected_wins']).round(2).astype(str) + " - " + gavi_stat_df['expected_wins'].round(2).astype(str)
        gavi_stat_df['delta'] = (gavi_stat_df['expected_wins'] - gavi_stat_df['win']).round(2)
    else:
        gavi_stat_df = df.groupby('Manager').agg(
            win=('win', 'sum'),
            loss=('win', 'count'),
            teams_beat_this_week=('teams_beat_this_week', 'sum')
        ).reset_index()
        gavi_stat_df['loss'] = gavi_stat_df['loss'] - gavi_stat_df['win']
        gavi_stat_df['record'] = gavi_stat_df['win'].astype(str) + " - " + gavi_stat_df['loss'].astype(str)
        gavi_stat_df['expected_wins'] = (gavi_stat_df['teams_beat_this_week'] / 9).round(2)
        gavi_stat_df['expected_record'] = gavi_stat_df['expected_wins'].round(2).astype(str) + " - " + (gavi_stat_df['win'] + gavi_stat_df['loss'] - gavi_stat_df['expected_wins']).round(2).astype(str)
        gavi_stat_df['delta'] = (gavi_stat_df['win'] - gavi_stat_df['expected_wins']).round(2)

    return gavi_stat_df

# Main function
def main():
    st.title("Simulations Viewer")

    # File uploader
    uploaded_file = st.file_uploader("Load Pickle File", type="pkl")
    if uploaded_file:
        df_dict = load_pickle_file(uploaded_file)
        if df_dict:
            df = df_dict.get('Matchup Data')
            if df is not None:
                years = df['year'].astype(str).unique().tolist()
                years.insert(0, "All Years")

                simulation_type = st.selectbox("Select Simulation Type", ["Gavi Stat", "Opponent Gavi Stat"])
                selected_year = st.selectbox("Select Year", years)
                include_playoffs = st.checkbox("Include Playoffs", value=True)
                include_regular_season = st.checkbox("Include Regular Season", value=True)

                if st.button("Calculate Simulation"):
                    if simulation_type == "Gavi Stat":
                        gavi_stat_df = calculate_gavi_stat(df, selected_year, include_playoffs)
                    else:
                        gavi_stat_df = calculate_gavi_stat(df, selected_year, include_playoffs, opponent=True)

                    st.write("Gavi Stat Results")
                    st.dataframe(gavi_stat_df)

if __name__ == "__main__":
    main()