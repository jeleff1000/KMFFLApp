import streamlit as st
import numpy as np
import pandas as pd

# -------------------------
# Config
# -------------------------
PLAYOFF_SLOTS = 6
BYE_SLOTS = 2
HALF_LIFE_WEEKS = 10
SHRINK_K = 6.0
SIGMA_FLOOR_MIN = 10
N_SIMS = 1000
RNG_SEED = 42

# -------------------------
# Helpers: keys & canonical
# -------------------------
def add_match_key(df):
    df = df.copy()
    df["mA"] = df[["Manager", "opponent"]].min(axis=1)
    df["mB"] = df[["Manager", "opponent"]].max(axis=1)
    df["match_key"] = list(zip(df["year"], df["week"], df["mA"], df["mB"]))
    return df

def canonicalize(df):
    df = df.copy()
    df["mA"] = df[["Manager", "opponent"]].min(axis=1)
    df["mB"] = df[["Manager", "opponent"]].max(axis=1)
    df["match_key"] = list(zip(df["year"], df["week"], df["mA"], df["mB"]))
    return df[df["Manager"] == df["mA"]]

# -------------------------
# Recency weights w/ early-season prior penalty
# -------------------------
def recency_weights(df, season, week, half_life, boundary_penalty=0.15):
    """Prior-season rows get an extra penalty early; fades out by ~Week 5."""
    hl = max(1, int(half_life))
    lam = np.log(2.0) / hl
    timeline = (df["year"] - season) * 100 + (df["week"] - week)
    weeks_ago = np.maximum(0, (-timeline).astype(float))
    base = np.exp(-lam * weeks_ago)

    prior = (df["year"] < season).astype(float)
    fade = min(1.0, max(0.0, (week - 1) / 4.0))  # 0 at W1 -> 1 by ~W5
    penalty = (1 - fade) * boundary_penalty + fade * 1.0
    return base * np.where(prior == 1.0, penalty, 1.0)

# -------------------------
# Win/points snapshot
# -------------------------
def wins_points_to_date(played_raw):
    tmp = add_match_key(played_raw)

    def _win_val(s):
        if len(s) < 2:
            return pd.Series([np.nan] * len(s), index=s.index)
        a, b = s.iloc[0], s.iloc[1]
        if a > b: return pd.Series([1.0, 0.0], index=s.index)
        if b > a: return pd.Series([0.0, 1.0], index=s.index)
        return pd.Series([0.5, 0.5], index=s.index)

    tmp["win_val"] = tmp.groupby("match_key")["team_points"].transform(lambda s: _win_val(s).values)
    wins = tmp.groupby("Manager")["win_val"].sum().astype(float)
    pts  = tmp.groupby("Manager")["team_points"].sum().astype(float)
    return wins, pts

# -------------------------
# Ranking/seeding
# -------------------------
def rank_and_seed(wins, points, playoff_slots, bye_slots, played_raw=None):
    managers = sorted(set(wins.index) | set(points.index))
    w = wins.reindex(managers).fillna(0.0)
    pf = points.reindex(managers).fillna(0.0)

    if played_raw is not None and len(played_raw) > 0:
        mgr_weeks = pd.concat([
            played_raw[["Manager", "year", "week"]].rename(columns={"Manager": "name"}),
            played_raw[["opponent", "year", "week"]].rename(columns={"opponent": "name"})
        ])
        games_played = (mgr_weeks.drop_duplicates()
                        .groupby("name").size()
                        .reindex(managers).fillna(0).astype(int))
    else:
        games_played = pd.Series(0, index=managers)

    l = (games_played - w).clip(lower=0)
    table = (pd.DataFrame({"Manager": managers, "W": w.values, "L": l.values, "PF": pf.values})
             .sort_values(["W", "PF"], ascending=[False, False])
             .reset_index(drop=True))
    table["seed"] = np.arange(1, len(table) + 1)
    table["made_playoffs"] = table["seed"] <= playoff_slots
    table["bye"] = table["seed"] <= bye_slots
    return table[["seed", "Manager", "W", "L", "PF", "made_playoffs", "bye"]]

# -------------------------
# Team models (EB shrink + capped prior + early bootstrap)
# -------------------------
def build_team_models(hist, season, week, half_life, shrink_k, sigma_floor,
                      boundary_penalty=0.15, prior_w_cap=2.0):
    h = hist.copy()
    h["w"] = recency_weights(h, season, week, half_life, boundary_penalty)

    # cap cumulative prior-season weight so prior can't dominate
    prior_mask = h["year"] < season
    if prior_mask.any():
        w_prior = (h.loc[prior_mask]
                   .groupby("Manager")["w"].transform(lambda s: s / max(1e-12, s.sum())))
        h.loc[prior_mask, "w"] = w_prior * prior_w_cap

    league_mu = h["team_points"].mean()
    league_sd = h["team_points"].std(ddof=1)

    by_mgr = (
        h.groupby("Manager")
         .apply(lambda g: pd.Series({
             "n": g.shape[0],
             "w_sum": g["w"].sum(),
             "mu_raw": (g["team_points"] * g["w"]).sum() / (g["w"].sum() + 1e-12),
             "sd_raw": g["team_points"].std(ddof=1) if len(g) >= 2 else np.nan,
         }))
    )

    # stronger shrink when weeks are tiny
    k = float(shrink_k)
    weeks_played = max(0, int(week))
    k_eff = k * max(1.0, (4 - min(weeks_played, 4)) * 0.75)

    w_eb = by_mgr["w_sum"] / (by_mgr["w_sum"] + k_eff)
    mu_hat = (w_eb * by_mgr["mu_raw"] + (1 - w_eb) * league_mu).to_dict()

    sd_fill = by_mgr["sd_raw"].fillna(league_sd * 0.9)
    sigma_floor = max(float(sigma_floor), league_sd * 0.35)
    sigma_hat = sd_fill.clip(lower=sigma_floor).to_dict()

    # bootstrap: prefer current-season only until Week <=3 if we have samples
    samples_by_team = {}
    for m, g in h.groupby("Manager"):
        g_cur = g[g["year"] == season]
        if week <= 3 and len(g_cur) >= 2:
            samples_by_team[m] = g_cur[["team_points", "w"]].copy()
        else:
            samples_by_team[m] = g[["team_points", "w"]].copy()

    # defaults for unseen managers
    for m in h["Manager"].unique():
        mu_hat.setdefault(m, league_mu)
        sigma_hat.setdefault(m, sigma_floor)

    return mu_hat, sigma_hat, samples_by_team, league_mu, sigma_floor

@st.cache_data
def _cached_models(df, season, week, half_life, shrink_k, sigma_floor,
                   boundary_penalty=0.15, prior_w_cap=2.0):
    return build_team_models(df, season, week, half_life, shrink_k, sigma_floor,
                             boundary_penalty=boundary_penalty, prior_w_cap=prior_w_cap)

def ensure_params_for_future(mu_hat, sigma_hat, samples_by_team, df_future, league_mu, sigma_floor):
    future_mgrs = set(df_future["Manager"]).union(set(df_future["opponent"]))
    for m in future_mgrs:
        mu_hat.setdefault(m, league_mu)
        sigma_hat.setdefault(m, sigma_floor)
        samples_by_team.setdefault(m, pd.DataFrame({"team_points": [], "w": []}))

# -------------------------
# Score draw
# -------------------------
def draw_score(manager, rng, mu_hat, sigma_hat, samples_by_team, use_bootstrap=True, bootstrap_min=4):
    samp = samples_by_team.get(manager)
    if use_bootstrap and samp is not None and len(samp) >= bootstrap_min and float(samp["w"].sum()) > 0:
        p = (samp["w"] / samp["w"].sum()).to_numpy()
        return float(rng.choice(samp["team_points"].to_numpy(), p=p))
    mu = mu_hat.get(manager, np.mean(list(mu_hat.values())))
    sd = sigma_hat.get(manager, np.mean(list(sigma_hat.values())))
    return float(max(0.0, rng.normal(mu, sd)))

# -------------------------
# Simulation helpers
# -------------------------
def _pair_quarters(top6, bye_slots=2):
    assert len(top6) == 6 and bye_slots == 2
    byes = top6[:bye_slots]
    qtrs = [(top6[2], top6[5]), (top6[3], top6[4])]
    return byes, qtrs

def _sim_game(a, b, rng, mu_hat, sigma_hat, samples_by_team):
    sa = draw_score(a, rng, mu_hat, sigma_hat, samples_by_team)
    sb = draw_score(b, rng, mu_hat, sigma_hat, samples_by_team)
    if sa > sb: return a
    if sb > sa: return b
    return rng.choice([a, b])

def simulate_playoff_bracket(seeds, playoff_schedule, rng, bye_slots=BYE_SLOTS,
                             current_week=None, mu_hat=None, sigma_hat=None, samples_by_team=None):
    playoff_mgrs = seeds.loc[seeds["made_playoffs"], "Manager"].tolist()
    playoff_weeks = sorted(playoff_schedule["week"].unique())
    future_weeks = [w for w in playoff_weeks if (current_week is None or w > current_week)]

    round2, round3, champ = set(), set(), None

    # round 1
    if len(future_weeks) >= 1:
        byes = playoff_mgrs[:bye_slots]
        qtrs = [(playoff_mgrs[2], playoff_mgrs[5]), (playoff_mgrs[3], playoff_mgrs[4])]
        r1_winners = list(byes)
        for a, b in qtrs:
            r1_winners.append(_sim_game(a, b, rng, mu_hat, sigma_hat, samples_by_team))
        round2.update(r1_winners)
    else:
        r1_winners = playoff_mgrs

    # semis (reseed)
    if len(future_weeks) >= 2:
        r2_mgrs = sorted(r1_winners, key=lambda m: seeds.loc[seeds["Manager"] == m, "seed"].values[0])
        semis = [(r2_mgrs[0], r2_mgrs[-1]), (r2_mgrs[1], r2_mgrs[-2])]
        r2_winners = []
        for a, b in semis:
            r2_winners.append(_sim_game(a, b, rng, mu_hat, sigma_hat, samples_by_team))
        round3.update(r2_winners)
    else:
        r2_winners = r1_winners

    # championship
    if len(future_weeks) >= 3 and len(r2_winners) == 2:
        champ = _sim_game(r2_winners[0], r2_winners[1], rng, mu_hat, sigma_hat, samples_by_team)

    return round2, round3, champ

def simulate_one(played_raw, future_canon, mu_hat, sigma_hat, samples_by_team, rng, playoff_slots, bye_slots):
    all_games = played_raw.copy()
    for _, row in future_canon.iterrows():
        score_a = draw_score(row["Manager"], rng, mu_hat, sigma_hat, samples_by_team)
        score_b = draw_score(row["opponent"], rng, mu_hat, sigma_hat, samples_by_team)
        new_row_a = row.copy(); new_row_a["team_points"] = score_a
        new_row_b = row.copy(); new_row_b["Manager"], new_row_b["opponent"] = row["opponent"], row["Manager"]
        new_row_b["team_points"] = score_b
        all_games = pd.concat([all_games, pd.DataFrame([new_row_a, new_row_b])], ignore_index=True)

    wins_to_date, pts_to_date = wins_points_to_date(all_games)
    return rank_and_seed(wins_to_date, pts_to_date, playoff_slots, bye_slots, played_raw=all_games)

# -------------------------
# Historical snapshots (no buckets) + kernels
# -------------------------
@st.cache_data
def _cached_history_snapshots(all_games, playoff_slots=PLAYOFF_SLOTS):
    """
    One row per (season, week, manager) with W, L, PF_pct, made_playoffs, final_seed.
    """
    rows = []
    seasons = sorted(all_games["year"].unique())

    for yr in seasons:
        reg = all_games[(all_games["year"] == yr) & (all_games["is_playoffs"] == 0)]
        if reg.empty:
            continue

        # final table for that season
        wins_f, pts_f = wins_points_to_date(reg)
        final_table = rank_and_seed(wins_f, pts_f, playoff_slots, BYE_SLOTS, played_raw=reg)
        final_seed_map = dict(zip(final_table["Manager"], final_table["seed"]))
        made = set(final_table.loc[final_table["made_playoffs"], "Manager"])

        weeks = sorted(reg["week"].unique())
        for w in weeks:
            played = reg[reg["week"] <= w]
            wins_w, pts_w = wins_points_to_date(played)
            gp = (pd.concat([
                    played[["Manager","year","week"]].rename(columns={"Manager":"name"}),
                    played[["opponent","year","week"]].rename(columns={"opponent":"name"})
                 ])
                 .drop_duplicates()
                 .groupby("name")["week"].nunique())

            mgrs = sorted(set(wins_w.index) | set(gp.index) | set(pts_w.index))
            if not mgrs:
                continue

            W  = wins_w.reindex(mgrs).fillna(0.0)
            PF = pts_w.reindex(mgrs).fillna(0.0)
            GP = gp.reindex(mgrs).fillna(0).astype(int)
            L  = (GP - W).clip(lower=0).astype(int)
            pf_pct = 100.0 * PF.rank(pct=True)

            for m in mgrs:
                rows.append({
                    "year": yr,
                    "week": int(w),
                    "Manager": m,
                    "W": float(W.loc[m]),
                    "L": float(L.loc[m]),
                    "PF_pct": float(pf_pct.loc[m]),
                    "made_playoffs": 1.0 if m in made else 0.0,
                    "final_seed": int(final_seed_map.get(m, np.nan))
                })

    return pd.DataFrame(rows)

def _league_base_rate(all_games, playoff_slots=PLAYOFF_SLOTS):
    sizes = []
    for yr in sorted(all_games["year"].unique()):
        reg = all_games[(all_games["year"] == yr) & (all_games["is_playoffs"] == 0)]
        n = reg["Manager"].nunique()
        if n > 0: sizes.append(n)
    if sizes:
        return float(np.clip(playoff_slots / np.mean(sizes), 0.0, 1.0))
    return 0.5

def _gaussian_kernel(d2):
    return np.exp(-0.5 * d2)

def empirical_kernel_playoff_prob(played_raw, week, history_snapshots,
                                  h_W=0.9, h_L=0.9, h_PF=15.0, h_week=0.9,
                                  prior_mean=0.5, prior_strength=6.0):
    """
    Nadaraya–Watson: returns {Manager: P(playoffs)} purely from history.
    """
    if played_raw.empty or history_snapshots.empty:
        return {}
    wins_w, pts_w = wins_points_to_date(played_raw)
    gp = (pd.concat([
            played_raw[["Manager","year","week"]].rename(columns={"Manager":"name"}),
            played_raw[["opponent","year","week"]].rename(columns={"opponent":"name"})
         ])
         .drop_duplicates()
         .groupby("name")["week"].nunique())
    mgrs = sorted(set(wins_w.index) | set(gp.index) | set(pts_w.index))
    if not mgrs: return {}

    W  = wins_w.reindex(mgrs).fillna(0.0)
    PF = pts_w.reindex(mgrs).fillna(0.0)
    GP = gp.reindex(mgrs).fillna(0).astype(int)
    L  = (GP - W).clip(lower=0).astype(int)
    pf_pct = 100.0 * PF.rank(pct=True)

    H = history_snapshots
    out = {}
    for m in mgrs:
        xW, xL, xPF, xwk = float(W.loc[m]), float(L.loc[m]), float(pf_pct.loc[m]), float(week)
        dW  = (H["W"].to_numpy()      - xW)  / max(1e-6, h_W)
        dL  = (H["L"].to_numpy()      - xL)  / max(1e-6, h_L)
        dPF = (H["PF_pct"].to_numpy() - xPF) / max(1e-6, h_PF)
        dWK = (H["week"].to_numpy()   - xwk) / max(1e-6, h_week)
        d2 = dW*dW + dL*dL + dPF*dPF + dWK*dWK
        w  = _gaussian_kernel(d2)

        num = float((w * H["made_playoffs"].to_numpy()).sum())
        den = float(w.sum())
        if den <= 1e-9:
            p_hat = prior_mean
        else:
            a0 = prior_mean * prior_strength
            b0 = (1.0 - prior_mean) * prior_strength
            p_hat = (num + a0) / (den + a0 + b0)

        out[m] = float(np.clip(p_hat, 0.0, 1.0))
    return out

def empirical_kernel_seed_dist(played_raw, week, history_snapshots, n_teams,
                               h_W=0.9, h_L=0.9, h_PF=15.0, h_week=0.9,
                               prior_strength=3.0):
    """
    Returns a DataFrame index=Manager, columns=1..n_teams with probabilities
    for each final seed, purely from historical neighbors.
    """
    if played_raw.empty or history_snapshots.empty:
        return pd.DataFrame()

    wins_w, pts_w = wins_points_to_date(played_raw)
    gp = (pd.concat([
            played_raw[["Manager","year","week"]].rename(columns={"Manager":"name"}),
            played_raw[["opponent","year","week"]].rename(columns={"opponent":"name"})
         ])
         .drop_duplicates()
         .groupby("name")["week"].nunique())
    mgrs = sorted(set(wins_w.index) | set(gp.index) | set(pts_w.index))
    if not mgrs:
        return pd.DataFrame()

    W  = wins_w.reindex(mgrs).fillna(0.0)
    PF = pts_w.reindex(mgrs).fillna(0.0)
    GP = gp.reindex(mgrs).fillna(0).astype(int)
    L  = (GP - W).clip(lower=0).astype(int)
    pf_pct = 100.0 * PF.rank(pct=True)

    H = history_snapshots.dropna(subset=["final_seed"]).copy()
    seeds = np.arange(1, n_teams + 1)
    cols = list(seeds)
    out = pd.DataFrame(0.0, index=mgrs, columns=cols)

    # uniform Dirichlet prior across seeds
    alpha0 = np.ones(n_teams) * (prior_strength / n_teams)

    H_seed = H["final_seed"].to_numpy()
    for m in mgrs:
        xW, xL, xPF, xwk = float(W.loc[m]), float(L.loc[m]), float(pf_pct.loc[m]), float(week)
        dW  = (H["W"].to_numpy()      - xW)  / max(1e-6, h_W)
        dL  = (H["L"].to_numpy()      - xL)  / max(1e-6, h_L)
        dPF = (H["PF_pct"].to_numpy() - xPF) / max(1e-6, h_PF)
        dWK = (H["week"].to_numpy()   - xwk) / max(1e-6, h_week)
        d2 = dW*dW + dL*dL + dPF*dPF + dWK*dWK
        w  = _gaussian_kernel(d2)

        # weighted counts per seed (1..n_teams)
        counts = np.zeros(n_teams)
        for k in range(1, n_teams + 1):
            counts[k-1] = float(w[(H_seed == k)].sum())

        probs = (counts + alpha0) / (counts.sum() + alpha0.sum() + 1e-12)
        out.loc[m, cols] = probs

    return out

# -------------------------
# UI
# -------------------------
class PlayoffOddsViewer:
    def __init__(self, matchup_data_df):
        self.df = matchup_data_df.copy()

    def display(self):
        st.subheader("Playoff Odds Monte Carlo Simulation")
        df = self.df[(self.df["is_consolation"] == 0)].copy()
        seasons = sorted(df["year"].unique())
        max_season = max(seasons)

        sim_mode = st.radio("Simulation Start", ["Start from Today", "Start from Specific Date"])
        if sim_mode == "Start from Today":
            season = max_season
            all_weeks = sorted(df[df["year"] == season]["week"].unique())
            week = max(all_weeks)
            go_clicked = st.button("Go")
        else:
            cols = st.columns([2, 2, 1])
            season = cols[0].selectbox("Select Season", seasons, index=len(seasons) - 1)
            all_weeks = sorted(df[df["year"] == season]["week"].unique())
            week = cols[1].selectbox("Select Week", all_weeks, index=len(all_weeks) - 1)
            go_clicked = cols[2].button("Go")

        reg_season_raw = df[(df["year"] == season) & (df["is_playoffs"] == 0)].copy()
        played_raw = reg_season_raw[reg_season_raw["week"] <= week].copy()
        future_canon = canonicalize(reg_season_raw[reg_season_raw["week"] > week].copy())
        n_teams = reg_season_raw["Manager"].nunique()

        sigma_floor_dynamic = SIGMA_FLOOR_MIN if week >= 3 else max(SIGMA_FLOOR_MIN, 14)
        mu_hat, sigma_hat, samples_by_team, league_mu, sigma_floor = _cached_models(
            df, season, week, HALF_LIFE_WEEKS, SHRINK_K, sigma_floor_dynamic,
            boundary_penalty=0.15, prior_w_cap=2.0
        )
        ensure_params_for_future(mu_hat, sigma_hat, samples_by_team, future_canon, league_mu, sigma_floor)

        playoff_schedule = df[(df["year"] == season) & (df["is_playoffs"] == 1)]
        playoff_weeks = sorted(playoff_schedule["week"].unique())

        if go_clicked:
            rng = np.random.default_rng(RNG_SEED)
            # Use regular season simulation viewer if there are future regular season games and not in playoffs
            if not future_canon.empty and week not in playoff_weeks:
                sims, playoff_r2, playoff_r3, champions = [], [], [], []
                for _ in range(N_SIMS):
                    seeds = simulate_one(played_raw, future_canon, mu_hat, sigma_hat, samples_by_team, rng,
                                         PLAYOFF_SLOTS, BYE_SLOTS)
                    r2, r3, champ = simulate_playoff_bracket(
                        seeds, playoff_schedule, rng, BYE_SLOTS,
                        current_week=None, mu_hat=mu_hat, sigma_hat=sigma_hat, samples_by_team=samples_by_team
                    )
                    playoff_r2.extend(r2)
                    playoff_r3.extend(r3)
                    if champ is not None:
                        champions.append(champ)
                    sims.append(seeds)
                tall = pd.concat(sims, ignore_index=True)
                odds = (tall.groupby("Manager")
                        .agg(P_Playoffs=("made_playoffs", "mean"),
                             P_Bye=("bye", "mean"),
                             Exp_Final_Wins=("W", "mean"),
                             Exp_Final_PF=("PF", "mean"))
                        .assign(P_Playoffs=lambda d: (100 * d.P_Playoffs).round(2),
                                P_Bye=lambda d: (100 * d.P_Bye).round(2),
                                Exp_Final_Wins=lambda d: d.Exp_Final_Wins.round(2),
                                Exp_Final_PF=lambda d: d.Exp_Final_PF.round(2)))
                odds["P_Semis"] = odds.index.map(lambda m: round(100 * playoff_r2.count(m) / N_SIMS, 2))
                odds["P_Final"] = odds.index.map(lambda m: round(100 * playoff_r3.count(m) / N_SIMS, 2))
                odds["P_Champ"] = odds.index.map(lambda m: round(100 * champions.count(m) / N_SIMS, 2))
                avg_seed = tall.groupby("Manager")["seed"].mean().round(2).rename("Avg_Seed")
                odds = odds.merge(avg_seed, left_index=True, right_index=True)

                # ----- Baseline (history) & blending weights
                history_snapshots = _cached_history_snapshots(df, PLAYOFF_SLOTS)
                p0 = _league_base_rate(df, PLAYOFF_SLOTS)
                baseline_playoff = empirical_kernel_playoff_prob(
                    played_raw, week, history_snapshots,
                    h_W=0.9, h_L=0.9, h_PF=15.0, h_week=0.9,
                    prior_mean=p0, prior_strength=6.0
                )
                sim_seed_dist = (
                    tall.pivot_table(index="Manager", columns="seed", values="W", aggfunc="size", fill_value=0)
                    .div(len(sims)))
                all_cols = list(range(1, n_teams + 1))
                sim_seed_dist = sim_seed_dist.reindex(columns=all_cols, fill_value=0.0)
                hist_seed_dist = empirical_kernel_seed_dist(
                    played_raw, week, history_snapshots, n_teams,
                    h_W=0.9, h_L=0.9, h_PF=15.0, h_week=0.9,
                    prior_strength=3.0
                ).reindex(index=sim_seed_dist.index, columns=all_cols, fill_value=0.0)
                weeks_played = int(played_raw["week"].nunique()) if not played_raw.empty else 0
                sim_w = 0.25 + 0.75 * min(1.0, max(0.0, (weeks_played - 1) / 4.0))
                base_w = 1.0 - sim_w

                odds = odds.copy()
                odds["P_Playoffs"] = odds.apply(
                    lambda r: round(
                        100.0 * (sim_w * (r["P_Playoffs"] / 100.0) + base_w * baseline_playoff.get(r.name, p0)), 2),
                    axis=1
                )
                odds["P_Bye"] = odds.index.map(
                    lambda m: round(100 * (sim_seed_dist.loc[m, 1] + sim_seed_dist.loc[m, 2]), 2))
                blended_seed = (sim_w * sim_seed_dist + base_w * hist_seed_dist) * 100.0
                blended_seed = blended_seed.round(2).reset_index()
                odds["P_Bye"] = odds.index.map(
                    lambda m: round(blended_seed.loc[blended_seed["Manager"] == m, 1].values[0] +
                                    blended_seed.loc[blended_seed["Manager"] == m, 2].values[0], 2)
                )
                odds = odds.sort_values("Avg_Seed", ascending=True).reset_index().rename(columns={"index": "Manager"})
                cols = ["Avg_Seed"] + [c for c in odds.columns if c != "Avg_Seed"]
                odds = odds[cols]
                playoff_total = odds["P_Playoffs"].sum()
                playoff_target = PLAYOFF_SLOTS * 100.0
                if playoff_total > 0:
                    odds["P_Playoffs"] = (odds["P_Playoffs"] * (playoff_target / playoff_total)).round(2)
                bye_total = odds["P_Bye"].sum()
                bye_target = BYE_SLOTS * 100.0
                if bye_total > 0:
                    odds["P_Bye"] = (odds["P_Bye"] * (bye_target / bye_total)).round(2)
                st.subheader("Simulation Odds")
                st.dataframe(odds, hide_index=True)
                st.subheader("Seed Distribution")
                st.dataframe(blended_seed, hide_index=True)
            else:
                # --- Actual playoff odds viewer ---
                sims, playoff_r2, playoff_r3, champions = [], [], [], []
                wins_to_date, pts_to_date = wins_points_to_date(played_raw)
                seeds = rank_and_seed(wins_to_date, pts_to_date, PLAYOFF_SLOTS, BYE_SLOTS, played_raw=played_raw)
                for _ in range(N_SIMS):
                    sim_seeds = seeds.copy()
                    actual_r2, actual_r3, actual_champ = [], [], None
                    for idx, pw in enumerate(playoff_weeks):
                        games = playoff_schedule[playoff_schedule["week"] == pw]
                        if pw <= week and not games.empty:
                            tmp = games.copy()
                            tmp["mA"] = tmp[["Manager", "opponent"]].min(axis=1)
                            tmp["mB"] = tmp[["Manager", "opponent"]].max(axis=1)
                            tmp["match_key"] = list(zip(tmp["year"], tmp["week"], tmp["mA"], tmp["mB"]))

                            def _win_val(s):
                                a, b = s.iloc[0], s.iloc[1]
                                if a > b: return pd.Series([1.0, 0.0], index=s.index)
                                if b > a: return pd.Series([0.0, 1.0], index=s.index)
                                return pd.Series([0.5, 0.5], index=s.index)

                            tmp["win_val"] = tmp.groupby("match_key")["team_points"].transform(
                                lambda s: _win_val(s).values)
                            winners = tmp[tmp["win_val"] == 1]["Manager"].tolist()
                            if idx == 0:
                                actual_r2 = winners
                            elif idx == 1:
                                actual_r3 = winners
                            elif idx == 2 and len(winners) == 1:
                                actual_champ = winners[0]
                        else:
                            if idx == 0:
                                byes, qtrs = _pair_quarters(
                                    sim_seeds.loc[sim_seeds["made_playoffs"], "Manager"].tolist(), BYE_SLOTS)
                                r2 = byes.copy()
                                for a, b in qtrs:
                                    winner = _sim_game(a, b, rng, mu_hat, sigma_hat, samples_by_team)
                                    r2.append(winner)
                                actual_r2 = r2
                            elif idx == 1 and actual_r2:
                                semis_seeds = [sim_seeds.loc[sim_seeds["Manager"] == m, "seed"].values[0] for m in
                                               actual_r2]
                                sorted_semis = [x for _, x in sorted(zip(semis_seeds, actual_r2))]
                                semi_pairs = [(sorted_semis[0], sorted_semis[3]), (sorted_semis[1], sorted_semis[2])]
                                r3 = []
                                for a, b in semi_pairs:
                                    winner = _sim_game(a, b, rng, mu_hat, sigma_hat, samples_by_team)
                                    r3.append(winner)
                                actual_r3 = r3
                            elif idx == 2 and actual_r3 and len(actual_r3) == 2:
                                champ = _sim_game(actual_r3[0], actual_r3[1], rng, mu_hat, sigma_hat, samples_by_team)
                                actual_champ = champ
                    playoff_r2.extend(actual_r2)
                    playoff_r3.extend(actual_r3)
                    if actual_champ is not None:
                        champions.append(actual_champ)
                    sims.append(sim_seeds)
                tall = pd.concat(sims, ignore_index=True)
                odds = (tall.groupby("Manager")
                        .agg(P_Playoffs=("made_playoffs", "mean"),
                             P_Bye=("bye", "mean"),
                             Exp_Final_Wins=("W", "mean"),
                             Exp_Final_PF=("PF", "mean"))
                        .assign(P_Playoffs=lambda d: (100 * d.P_Playoffs).round(2),
                                P_Bye=lambda d: (100 * d.P_Bye).round(2),
                                Exp_Final_Wins=lambda d: d.Exp_Final_Wins.round(2),
                                Exp_Final_PF=lambda d: d.Exp_Final_PF.round(2)))
                odds["P_Semis"] = odds.index.map(lambda m: round(100 * playoff_r2.count(m) / N_SIMS, 2))
                odds["P_Final"] = odds.index.map(lambda m: round(100 * playoff_r3.count(m) / N_SIMS, 2))
                odds["P_Champ"] = odds.index.map(lambda m: round(100 * champions.count(m) / N_SIMS, 2))
                avg_seed = tall.groupby("Manager")["seed"].mean().round(2).rename("Avg_Seed")
                odds = odds.merge(avg_seed, left_index=True, right_index=True)
                odds = odds.sort_values("Avg_Seed", ascending=True).reset_index().rename(columns={"index": "Manager"})
                cols = ["Avg_Seed"] + [c for c in odds.columns if c != "Avg_Seed"]
                odds = odds[cols]
                st.subheader("Playoff Odds")
                st.dataframe(odds, hide_index=True)
                seed_dist = (tall.pivot_table(index="Manager", columns="seed", values="W", aggfunc="size", fill_value=0)
                             .div(len(sims)).mul(100).round(2).sort_index(axis=1))
                st.subheader("Seed Distribution (%)")
                st.dataframe(seed_dist.reset_index(), hide_index=True)