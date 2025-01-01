import streamlit as st
import plotly.graph_objects as go
import pandas as pd

class PlayoffBracketsViewer:
    def __init__(self, df):
        self.df = df

    def create_bracket(self, year):
        # Filter the DataFrame for the selected year
        year_df = self.df[self.df['year'] == year]
        playoff_weeks = year_df[year_df['is_playoffs'] == 1]['week'].unique()
        if len(playoff_weeks) == 0:
            st.error("No playoff weeks found for the selected year")
            return go.Figure()

        # Create a figure
        fig = go.Figure()

        # Function to determine the winner
        def get_winner(team1, team2):
            if team1['team_points'] > team2['opponent_score']:
                return team1
            else:
                return team2

        # Initialize the current round teams
        current_round_teams = year_df[(year_df['week'] == playoff_weeks[0]) & (year_df['win'] == 1)]

        round_num = 1
        while len(current_round_teams) > 1:
            next_round_teams = []
            for i in range(0, len(current_round_teams), 2):
                if i + 1 < len(current_round_teams):
                    team1 = current_round_teams.iloc[i]
                    team2 = current_round_teams.iloc[i + 1]
                    winner = get_winner(team1, team2)
                    next_round_teams.append(winner)

                    # Add lines and text for the current round
                    y_pos = i + 1
                    fig.add_shape(type="line", x0=round_num - 0.5, y0=y_pos, x1=round_num + 0.5, y1=y_pos, line=dict(color="black"))
                    fig.add_annotation(x=round_num - 0.75, y=y_pos, text=f"{team1['Manager']} ({team1['team_points']})", showarrow=False, xanchor='right')
                    fig.add_annotation(x=round_num - 0.75, y=y_pos + 1, text=f"{team2['Manager']} ({team2['opponent_score']})", showarrow=False, xanchor='right')

            current_round_teams = pd.DataFrame(next_round_teams)
            round_num += 1

        # Add lines and text for the championship
        if len(current_round_teams) == 1:
            championship_winner = current_round_teams.iloc[0]
            fig.add_shape(type="line", x0=round_num - 0.5, y0=1.5, x1=round_num + 0.5, y1=1.5, line=dict(color="black"))
            fig.add_annotation(x=round_num - 0.75, y=1.5, text=f"{championship_winner['Manager']} ({championship_winner['team_points']})", showarrow=False, xanchor='right')

        # Adjust layout for the bracket
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=100),  # Increase bottom margin to lower the bracket
            height=800,  # Increase height for a bigger bracket
            width=1000  # Increase width for a bigger bracket
        )

        return fig

    def display(self):
        st.header("Playoff Brackets")

        # Dropdown for selecting the year
        years = sorted(self.df['year'].unique().tolist())
        selected_year = st.selectbox("Select Year", years)

        # Create and display the bracket for the selected year
        fig = self.create_bracket(selected_year)
        st.plotly_chart(fig)