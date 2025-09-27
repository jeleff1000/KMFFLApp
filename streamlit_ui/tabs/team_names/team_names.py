import streamlit as st

def display_team_names(matchup_data):
    st.header("Team Names")
    if matchup_data is not None and {'Manager', 'year', 'name'}.issubset(matchup_data.columns):
        data = matchup_data.copy()
        manager_options = ['All'] + sorted(data['Manager'].unique())
        year_options = ['All'] + sorted(data['year'].unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_manager = st.selectbox('Select Manager', manager_options)
        with col2:
            selected_year = st.selectbox('Select Year', year_options)

        if selected_manager != 'All':
            data = data[data['Manager'] == selected_manager]
        if selected_year != 'All':
            data = data[data['year'] == selected_year]

        data['year'] = data['year'].astype(str)
        data = data.drop_duplicates(subset=['name', 'year'])

        st.dataframe(data[['Manager', 'name', 'year']], hide_index=True)
    else:
        st.error("Matchup Data not found or missing required columns.")