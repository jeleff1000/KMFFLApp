import duckdb
import pandas as pd
import streamlit as st


class H2HViewer:
    """
    Renders either:
      - mode='h2h': standard head-to-head table for a single matchup_name
      - mode='league_optimal': single-table "League-Wide Optimal" lineup for year/week
        using players with league_wide_optimal_player == 1
    """

    def __init__(self, filtered_data: pd.DataFrame, matchup_data: pd.DataFrame):
        # Assumes filtered_data has been pre-filtered to Year/Week by the caller
        self.filtered_data = filtered_data.copy()
        self.matchup_data = matchup_data.copy()

        # Normalize types
        for frame in (self.filtered_data, self.matchup_data):
            for col in ["year", "week"]:
                if col in frame.columns:
                    frame[col] = pd.to_numeric(frame[col], errors="coerce")

        # Optional rename if matchup_data uses 'team' instead of 'team_name'
        mcols = {c.lower(): c for c in self.matchup_data.columns}
        if "team_name" not in self.matchup_data.columns and "team" in mcols:
            self.matchup_data = self.matchup_data.rename(columns={mcols["team"]: "team_name"})

        self.default_headshot = "https://static.www.nfl.com/image/private/f_auto,q_auto/league/mdrlzgankwwjldxllgcx"
        self.position_order = ["QB", "RB", "WR", "TE", "W/R/T", "K", "DEF"]
        self.bench_ir_positions = ["BN", "IR"]

    # ---------------------------
    # Public entry point
    # ---------------------------
    def display(self, prefix: str, mode: str = "h2h", matchup_name: str | None = None):
        if mode == "league_optimal":
            self._display_league_optimal(prefix)
        elif mode == "h2h":
            if not matchup_name:
                st.error("No matchup_name provided for H2H.")
                return
            self._display_h2h(prefix, matchup_name)
        else:
            st.error(f"Unknown mode '{mode}'. Expected 'h2h' or 'league_optimal'.")

    # ---------------------------
    # League-wide optimal (single team)
    # ---------------------------
    def _display_league_optimal(self, prefix: str):
        if "league_wide_optimal_player" not in self.filtered_data.columns:
            st.error("Column 'league_wide_optimal_player' is missing.")
            return

        # Select optimal players for this year/week
        df = self.filtered_data.copy()
        if {"year", "week"} <= set(df.columns):
            # Ensure we're truly on a single year/week slice
            years = sorted(df["year"].dropna().astype(int).unique())
            weeks = sorted(df["week"].dropna().astype(int).unique())
            if len(years) != 1 or len(weeks) != 1:
                st.warning("League Optimal requires a single Year/Week slice. Taking the max available.")
                y = int(df["year"].dropna().astype(int).max())
                w = int(df.loc[df["year"] == y, "week"].dropna().astype(int).max())
                df = df[(df["year"] == y) & (df["week"] == w)].copy()

        optimal = df[df["league_wide_optimal_player"] == 1].copy()
        if optimal.empty:
            st.warning("No players flagged as league_wide_optimal_player == 1 for this Year/Week.")
            return

        # Keep columns needed for the single-side table
        # Expect: player, fantasy_position, points, headshot_url
        for needed in ["player", "fantasy_position", "points"]:
            if needed not in optimal.columns:
                st.error(f"Missing column '{needed}' required for League-Wide Optimal view.")
                return
        if "headshot_url" not in optimal.columns:
            optimal["headshot_url"] = self.default_headshot

        # Build a single-side table ordered by position and slot within position
        single = self._prepare_single_side(optimal, "player", "points", "fantasy_position", "headshot_url")
        single["points_1"] = single["points"].round(2)
        single["player_1"] = single["player"]
        single["headshot_url_1"] = single["headshot_url"]

        # Columns for empty opponent side to reuse the same renderer
        single["points_2"] = 0.0
        single["player_2"] = ""
        single["headshot_url_2"] = ""

        # Calculate totals
        total_row = {
            "player_1": "Total",
            "points_1": round(single["points_1"].sum(), 2),
            "fantasy_position": "",
            "points_2": round(single["points_2"].sum(), 2),
            "player_2": "",
            "headshot_url_1": "",
            "headshot_url_2": ""
        }
        single = pd.concat([single, pd.DataFrame([total_row])], ignore_index=True)

        # Render using the same table style (one side filled, the other empty)
        self._render_table(
            df=single,
            team_1_name="League-Wide Optimal",
            team_2_name="",
            color_coding=False  # margins vs empty side aren't meaningful
        )

    # ---------------------------
    # H2H table (two teams)
    # ---------------------------
    def _display_h2h(self, prefix: str, matchup_name: str):
        # Work from the already year/week filtered self.filtered_data
        f = self.filtered_data.copy()
        if "matchup_name" not in f.columns:
            st.error("Column 'matchup_name' is missing in player data.")
            return
        f = f[f["matchup_name"].astype(str) == str(matchup_name)]
        if f.empty:
            st.warning(f"No rows for matchup '{matchup_name}'.")
            return

        # Join to matchup_data on keys
        con = duckdb.connect()
        con.register("filtered", f)
        con.register("matchup", self.matchup_data)

        merged = con.execute("""
            SELECT
                f.*,
                f.team_1 AS team_1,
                f.team_2 AS team_2
            FROM filtered f
            INNER JOIN matchup m
              ON f.manager  = m.manager
             AND f.opponent = m.opponent
             AND f.week     = m.week
             AND f.year     = m.year
        """).df()
        con.close()

        required_cols = ["team_1", "team_2", "player", "points", "fantasy_position", "manager", "headshot_url"]
        missing = [c for c in required_cols if c not in merged.columns]
        if missing:
            st.error(f"Missing required columns for H2H: {missing}")
            return

        # Prepare two sides
        team_1 = merged["team_1"].dropna().astype(str).iloc[0] if not merged["team_1"].dropna().empty else "Team 1"
        team_2 = merged["team_2"].dropna().astype(str).iloc[0] if not merged["team_2"].dropna().empty else "Team 2"

        t1 = self._prepare_team(merged, manager=team_1, player_col="player", points_col="points",
                                fantasy_pos_col="fantasy_position", headshot_col="headshot_url")
        t2 = self._prepare_team(merged, manager=team_2, player_col="player", points_col="points",
                                fantasy_pos_col="fantasy_position", headshot_col="headshot_url")

        # Align rows by position & slot
        aligned = t1.merge(
            t2[["fantasy_position", "slot", "player_2", "points_2", "headshot_url_2", "team_2"]],
            on=["fantasy_position", "slot"], how="outer"
        ).sort_values(["position_order", "slot"]).reset_index(drop=True)

        # Totals
        totals = {
            "player_1": "Total",
            "points_1": round(aligned["points_1"].fillna(0).sum(), 2),
            "fantasy_position": "",
            "points_2": round(aligned["points_2"].fillna(0).sum(), 2),
            "player_2": "",
            "headshot_url_1": "",
            "headshot_url_2": ""
        }
        aligned = pd.concat([aligned, pd.DataFrame([totals])], ignore_index=True)

        # Render
        self._render_table(aligned, team_1_name=team_1, team_2_name=team_2, color_coding=True)

    # ---------------------------
    # Helpers to prepare rows
    # ---------------------------
    def _prepare_single_side(self, df: pd.DataFrame, player_col: str, points_col: str,
                             fantasy_pos_col: str, headshot_col: str) -> pd.DataFrame:
        # Keep only main positions + W/R/T for the single table
        keep_positions = set(self.position_order + self.bench_ir_positions)
        df = df[df[fantasy_pos_col].isin(keep_positions)].copy()

        # Slot within position by points desc
        df["_pos_order"] = df[fantasy_pos_col].map({p: i for i, p in enumerate(self.position_order)}).fillna(999)
        df = df.sort_values(["_pos_order", points_col], ascending=[True, False]).copy()
        df["slot"] = df.groupby(fantasy_pos_col).cumcount()
        df.rename(columns={
            player_col: "player",
            points_col: "points",
            fantasy_pos_col: "fantasy_position",
            headshot_col: "headshot_url"
        }, inplace=True)
        return df[["fantasy_position", "player", "points", "headshot_url", "slot"]]

    def _prepare_team(self, merged: pd.DataFrame, manager: str, player_col: str, points_col: str,
                      fantasy_pos_col: str, headshot_col: str) -> pd.DataFrame:
        df = merged.copy()
        df = df[df["manager"].astype(str) == str(manager)].copy()

        # Fill headshots
        if headshot_col not in df.columns:
            df[headshot_col] = self.default_headshot
        df[headshot_col] = df[headshot_col].fillna(self.default_headshot).replace("", self.default_headshot)

        # Restrict to displayable positions
        df = df[df[fantasy_pos_col].isin(self.position_order + self.bench_ir_positions)].copy()

        # Order within position by points desc
        df["_pos_order"] = df[fantasy_pos_col].map({p: i for i, p in enumerate(self.position_order)}).fillna(999)
        df = df.sort_values(["_pos_order", points_col], ascending=[True, False]).copy()
        df["slot"] = df.groupby(fantasy_pos_col).cumcount()

        # Standardize cols for merge
        out = df[[fantasy_pos_col, player_col, points_col, headshot_col]].copy()
        out.rename(columns={
            fantasy_pos_col: "fantasy_position",
            player_col: "player_1",
            points_col: "points_1",
            headshot_col: "headshot_url_1"
        }, inplace=True)
        out["team_1"] = manager
        out["position_order"] = out["fantasy_position"].map({p: i for i, p in enumerate(self.position_order)}).fillna(999)
        out["slot"] = df["slot"].values

        # Also prepare side-2 labeled columns (for the other team path)
        side2 = out.rename(columns={
            "player_1": "player_2",
            "points_1": "points_2",
            "headshot_url_1": "headshot_url_2",
            "team_1": "team_2",
        })
        side2["team_2"] = manager

        # Return only side-1 labeled cols for align, plus position & slot
        return out[[
            "fantasy_position", "slot",
            "player_1", "points_1", "headshot_url_1", "team_1",
            "position_order"
        ]]

    # ---------------------------
    # Renderer
    # ---------------------------
    def _render_table(self, df: pd.DataFrame, team_1_name: str, team_2_name: str, color_coding: bool):
        st.markdown(
            """
            <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #f7f7f7; }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Pre-calc colors if needed
        if color_coding and {"margin_1", "margin_2"} <= set(df.columns):
            m1 = df["points_1"].fillna(0) - df["points_2"].fillna(0)
            m2 = -m1
            df = df.copy()
            df["margin_1"] = m1
            df["margin_2"] = m2
            gmin = min(df["margin_1"].min(), df["margin_2"].min())
            gmax = max(df["margin_1"].max(), df["margin_2"].max())
            span = max(gmax - gmin, 1e-9)
        else:
            gmin = gmax = 0
            span = 1

        def color_for(val):
            # green to red scale
            x = (val - gmin) / span
            r = int(255 - 200 * x)
            g = int(55 + 200 * x)
            b = 55
            return f"rgb({r},{g},{b})"

        # Build HTML table
        html = []
        html.append("<table>")
        html.append("<thead><tr>")
        html.append(f"<th colspan='2' style='font-size:16px;font-weight:bold;'>{team_1_name}</th>")
        html.append("<th style='font-size:16px;font-weight:bold;'>vs</th>")
        html.append(f"<th colspan='2' style='font-size:16px;font-weight:bold;'>{team_2_name}</th>")
        html.append("</tr></thead><tbody>")

        for _, row in df.iterrows():
            is_total = str(row.get("player_1", "")) == "Total"
            p1 = row.get("points_1", "")
            p2 = row.get("points_2", "")
            pos = row.get("fantasy_position", "")
            img1 = row.get("headshot_url_1", "")
            img2 = row.get("headshot_url_2", "")

            if color_coding and not is_total:
                c1 = color_for(float(row.get("points_1", 0) - row.get("points_2", 0)))
                c2 = color_for(float(row.get("points_2", 0) - row.get("points_1", 0)))
            else:
                c1 = c2 = "white"

            html.append("<tr>")
            html.append(f"<td><img src='{img1}' width='50'><br>{row.get('player_1','')}</td>")
            html.append(f"<td style='background-color:{c1};font-weight:bold;color:black;'>{p1}</td>")
            html.append(f"<td>{pos}</td>")
            html.append(f"<td style='background-color:{c2};font-weight:bold;color:black;'>{p2}</td>")
            html.append(f"<td><img src='{img2}' width='50'><br>{row.get('player_2','')}</td>")
            html.append("</tr>")

        html.append("</tbody></table>")
        st.markdown("".join(html), unsafe_allow_html=True)
