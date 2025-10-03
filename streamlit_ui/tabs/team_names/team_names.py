import streamlit as st

def display_team_names(matchup_data):
    st.header("Team Names")
    if matchup_data is not None and {'manager', 'year', 'team_name'}.issubset(matchup_data.columns):
        data = matchup_data.copy()
        manager_options = ['All'] + sorted(data['manager'].unique())
        year_options = ['All'] + sorted(data['year'].unique())

        col1, col2 = st.columns(2)
        with col1:
            selected_manager = st.selectbox('Select manager', manager_options)
        with col2:
            selected_year = st.selectbox('Select Year', year_options)

        if selected_manager != 'All':
            data = data[data['manager'] == selected_manager]
        if selected_year != 'All':
            data = data[data['year'] == selected_year]

        data['year'] = data['year'].astype(str)
        data = data.drop_duplicates(subset=['team_name', 'year'])

        st.dataframe(data[['manager', 'team_name', 'year']], hide_index=True)
    else:
        st.error("Matchup Data not found or missing required columns.")