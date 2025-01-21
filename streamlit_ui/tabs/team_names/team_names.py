import streamlit as st

def display_team_names(matchup_data):
    st.header("Team Names")
    if matchup_data is not None:
        # Add dropdowns for Manager and year
        manager_options = ['All'] + list(matchup_data['Manager'].unique())
        year_options = ['All'] + list(matchup_data['year'].unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_manager = st.selectbox('Select Manager', manager_options)
        with col2:
            selected_year = st.selectbox('Select Year', year_options)

        # Filter the data based on the selected options
        if selected_manager != 'All':
            matchup_data = matchup_data[matchup_data['Manager'] == selected_manager]
        if selected_year != 'All':
            matchup_data = matchup_data[matchup_data['year'] == selected_year]

        # Ensure the year column does not have a comma
        matchup_data['year'] = matchup_data['year'].astype(str)

        # Drop duplicates in the name column
        matchup_data = matchup_data.drop_duplicates(subset=['name', 'year'])

        # Display the filtered data
        st.dataframe(matchup_data[['Manager', 'name', 'year']], hide_index=True)
    else:
        st.error("Matchup Data not found.")