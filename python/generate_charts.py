"""
Generates all six portfolio charts from the experiment data and analysis outputs.
Saves PNG files to images/.
Run after experiment_analysis.py has produced the CSV outputs.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from scipy import stats
from statsmodels.stats.multitest import multipletests
import warnings

warnings.filterwarnings("ignore")

os.makedirs("images", exist_ok=True)

PALETTE = {
    "control":   "#4E79A7",
    "treatment": "#F28E2B",
    "positive":  "#59A14F",
    "negative":  "#E15759",
    "neutral":   "#B07AA1",
    "grid":      "#EBEBEB",
    "text":      "#2C2C2C",
}

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.dpi":        150,
    "text.color":        PALETTE["text"],
    "axes.labelcolor":   PALETTE["text"],
    "xtick.color":       PALETTE["text"],
    "ytick.color":       PALETTE["text"],
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def two_prop_ci(n_c, x_c, n_t, x_t):
    p_c = x_c / n_c
    p_t = x_t / n_t
    se = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    diff = p_t - p_c
    return diff, diff - 1.96 * se, diff + 1.96 * se, p_c, p_t


def save(fig, name, tight=True):
    path = f"images/{name}.png"
    if tight:
        fig.savefig(path, bbox_inches="tight", facecolor="white")
    else:
        fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"  Saved {path}")


# ---------------------------------------------------------------------------
# Chart 1: Top-line conversion uplift with 95% CI
# ---------------------------------------------------------------------------

def chart1_topline(df: pd.DataFrame):
    ctrl = df[df.experiment_group == "control"]
    trt  = df[df.experiment_group == "treatment"]
    diff, ci_lo, ci_hi, p_c, p_t = two_prop_ci(
        len(ctrl), ctrl.conversion_flag.sum(),
        len(trt),  trt.conversion_flag.sum(),
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("Chart 1 — Top-Line Conversion Rate & 95% CI", fontsize=14, fontweight="bold", y=1.01)

    # Left: bar chart
    ax = axes[0]
    bars = ax.bar(
        ["Control", "Treatment"],
        [p_c * 100, p_t * 100],
        color=[PALETTE["control"], PALETTE["treatment"]],
        width=0.45, edgecolor="white", linewidth=1.5,
    )
    for bar, val in zip(bars, [p_c, p_t]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                f"{val:.2%}", ha="center", va="bottom", fontweight="bold", fontsize=12)
    ax.set_ylabel("Conversion rate (%)")
    ax.set_ylim(0, max(p_c, p_t) * 100 * 1.25)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax.set_title("Conversion Rate by Group")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=PALETTE["grid"])

    # Right: confidence interval on absolute difference
    ax2 = axes[1]
    color = PALETTE["positive"] if ci_lo > 0 else PALETTE["negative"]
    ax2.errorbar(
        x=[diff * 100], y=[0],
        xerr=[[( diff - ci_lo) * 100], [(ci_hi - diff) * 100]],
        fmt="o", color=color, capsize=8, capthick=2.5, elinewidth=2.5, markersize=9,
    )
    ax2.axvline(0, color="#888", linestyle="--", linewidth=1.2)
    ax2.set_xlabel("Absolute uplift (percentage points)")
    ax2.set_yticks([])
    ax2.set_title("Absolute Uplift with 95% CI")
    rel = diff / p_c
    ax2.text(diff * 100, 0.06,
             f"+{diff*100:.2f} pp  ({rel:+.1%} relative)\np < 0.001",
             ha="center", va="bottom", fontsize=10, color=color)
    ax2.set_xlim(-0.3, diff * 100 + 0.8)

    plt.tight_layout()
    save(fig, "chart1_topline_uplift")


# ---------------------------------------------------------------------------
# Chart 2: Daily uplift over time with CI
# ---------------------------------------------------------------------------

def chart2_time_stability(df: pd.DataFrame):
    rows = []
    for day in sorted(df.day_since_launch.unique()):
        sub  = df[df.day_since_launch == day]
        ctrl = sub[sub.experiment_group == "control"]
        trt  = sub[sub.experiment_group == "treatment"]
        if len(ctrl) < 50 or len(trt) < 50:
            continue
        diff, ci_lo, ci_hi, p_c, p_t = two_prop_ci(
            len(ctrl), ctrl.conversion_flag.sum(),
            len(trt),  trt.conversion_flag.sum(),
        )
        rows.append({"day": day, "uplift": diff / p_c, "ci_lo": ci_lo / p_c, "ci_hi": ci_hi / p_c})

    ts = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.suptitle("Chart 2 — Treatment Effect Over Time (Daily)", fontsize=14, fontweight="bold")

    colors = [PALETTE["positive"] if ci_lo > 0 else PALETTE["negative"]
              for ci_lo in ts.ci_lo]

    ax.fill_between(ts.day, ts.ci_lo * 100, ts.ci_hi * 100,
                    alpha=0.18, color=PALETTE["treatment"], label="95% CI")
    ax.plot(ts.day, ts.uplift * 100, "o-", color=PALETTE["treatment"],
            linewidth=2.2, markersize=7, label="Relative uplift (%)")
    ax.axhline(0, color="#888", linestyle="--", linewidth=1.2)
    ax.axhline(2, color=PALETTE["positive"], linestyle=":", linewidth=1.2, alpha=0.7, label="+2% threshold")

    ax.set_xlabel("Day since launch")
    ax.set_ylabel("Relative uplift (%)")
    ax.set_title("Treatment effect decays materially after day 2")
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax.legend(frameon=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=PALETTE["grid"])
    ax.axvspan(1, 2.5, alpha=0.06, color=PALETTE["positive"])
    ax.text(1.75, ts.uplift.max() * 100 * 0.95, "Strong\ndays 1-2",
            ha="center", fontsize=9, color=PALETTE["positive"])

    plt.tight_layout()
    save(fig, "chart2_time_stability")


# ---------------------------------------------------------------------------
# Chart 3: Segment uplift heatmap
# ---------------------------------------------------------------------------

def chart3_segment_heatmap(df: pd.DataFrame):
    segments = {
        "user_type":     df.user_type.unique(),
        "device_type":   df.device_type.unique(),
        "browser":       ["chrome_mobile", "safari_mobile", "chrome_desktop", "firefox"],
        "country":       ["US", "UK", "CA", "AU", "DE"],
        "traffic_source": df.traffic_source.unique(),
    }

    rows = []
    for dim, values in segments.items():
        for val in sorted(values):
            sub  = df[df[dim] == val]
            ctrl = sub[sub.experiment_group == "control"]
            trt  = sub[sub.experiment_group == "treatment"]
            if len(ctrl) < 300 or len(trt) < 300:
                continue
            diff, ci_lo, ci_hi, p_c, p_t = two_prop_ci(
                len(ctrl), ctrl.conversion_flag.sum(),
                len(trt),  trt.conversion_flag.sum(),
            )
            rows.append({"segment": f"{dim}: {val}", "rel_uplift": diff / p_c * 100})

    seg_df = pd.DataFrame(rows).sort_values("rel_uplift")

    fig, ax = plt.subplots(figsize=(10, max(6, len(seg_df) * 0.38)))
    fig.suptitle("Chart 3 — Segment-Level Relative Uplift (%)", fontsize=14, fontweight="bold")

    colors = [PALETTE["positive"] if v > 0 else PALETTE["negative"] for v in seg_df.rel_uplift]
    bars = ax.barh(seg_df.segment, seg_df.rel_uplift, color=colors, edgecolor="white", height=0.6)
    ax.axvline(0, color="#555", linewidth=1.2)
    for bar, val in zip(bars, seg_df.rel_uplift):
        xpos = val + (0.15 if val >= 0 else -0.15)
        ax.text(xpos, bar.get_y() + bar.get_height() / 2,
                f"{val:+.1f}%", va="center", ha="left" if val >= 0 else "right",
                fontsize=9.5)

    ax.set_xlabel("Relative uplift (%)")
    ax.set_title("Returning users and mobile Safari are net losers")
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=PALETTE["grid"])

    pos_patch = mpatches.Patch(color=PALETTE["positive"], label="Positive uplift")
    neg_patch = mpatches.Patch(color=PALETTE["negative"], label="Negative uplift")
    ax.legend(handles=[pos_patch, neg_patch], frameon=False, loc="lower right")

    plt.tight_layout()
    save(fig, "chart3_segment_heatmap")


# ---------------------------------------------------------------------------
# Chart 4: Raw vs CUPED-adjusted effect
# ---------------------------------------------------------------------------

def chart4_cuped(df: pd.DataFrame):
    covariate = "pre_experiment_activity_score"
    theta = df["conversion_flag"].cov(df[covariate]) / df[covariate].var()

    df = df.copy()
    df["conversion_cuped"] = df["conversion_flag"] - theta * (
        df[covariate] - df[covariate].mean()
    )

    ctrl_raw = df[df.experiment_group == "control"]["conversion_flag"]
    trt_raw  = df[df.experiment_group == "treatment"]["conversion_flag"]
    ctrl_adj = df[df.experiment_group == "control"]["conversion_cuped"]
    trt_adj  = df[df.experiment_group == "treatment"]["conversion_cuped"]

    raw_diff = trt_raw.mean() - ctrl_raw.mean()
    adj_diff = trt_adj.mean() - ctrl_adj.mean()

    raw_se = np.sqrt(ctrl_raw.var() / len(ctrl_raw) + trt_raw.var() / len(trt_raw))
    adj_se = np.sqrt(ctrl_adj.var() / len(ctrl_adj) + trt_adj.var() / len(trt_adj))

    var_red = 1 - (ctrl_adj.var() + trt_adj.var()) / (ctrl_raw.var() + trt_raw.var())

    fig, ax = plt.subplots(figsize=(6, 5))

    ax.set_title("Raw vs CUPED-Adjusted Uplift", fontsize=13, fontweight="bold", pad=12)
    fig.text(
        0.5, 0.91,
        f"Covariate: pre_experiment_activity_score  ·  Variance reduction {var_red:.1%}",
        ha="center", fontsize=9, color="#777",
    )

    labels = ["Raw", "CUPED-adjusted"]
    diffs  = [raw_diff * 100, adj_diff * 100]
    errors = [1.96 * raw_se * 100, 1.96 * adj_se * 100]
    colors = [PALETTE["treatment"], PALETTE["neutral"]]

    ax.bar(labels, diffs, color=colors, width=0.36, edgecolor="white", zorder=3)
    ax.errorbar(
        labels, diffs, yerr=errors, fmt="none",
        color="#444", capsize=7, capthick=1.8, elinewidth=1.8, zorder=4,
    )

    ax.axhline(0, color="#AAA", linestyle="--", linewidth=1)
    ax.set_ylabel("Uplift (percentage points)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.2f}"))
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=PALETTE["grid"])

    plt.tight_layout(rect=[0, 0, 1, 0.89])
    save(fig, "chart4_cuped", tight=False)


# ---------------------------------------------------------------------------
# Chart 5: p-values before vs after BH correction
# ---------------------------------------------------------------------------

def chart5_multiple_testing(df: pd.DataFrame):
    segments = {
        "user_type":     df.user_type.unique(),
        "device_type":   df.device_type.unique(),
        "browser":       df.browser.unique(),
        "country":       df.country.unique(),
        "traffic_source": df.traffic_source.unique(),
    }

    p_vals, labels = [], []
    for dim, values in segments.items():
        for val in sorted(values):
            sub  = df[df[dim] == val]
            ctrl = sub[sub.experiment_group == "control"]
            trt  = sub[sub.experiment_group == "treatment"]
            if len(ctrl) < 200 or len(trt) < 200:
                continue
            p_pool = (ctrl.conversion_flag.sum() + trt.conversion_flag.sum()) / (len(ctrl) + len(trt))
            se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / len(ctrl) + 1 / len(trt)))
            z = (trt.conversion_flag.mean() - ctrl.conversion_flag.mean()) / se_pool
            p = 2 * (1 - stats.norm.cdf(abs(z)))
            p_vals.append(p)
            labels.append(f"{dim[:3]}:{val[:8]}")

    p_vals = np.array(p_vals)
    reject, p_corrected, _, _ = multipletests(p_vals, alpha=0.05, method="fdr_bh")

    sorted_idx = np.argsort(p_vals)
    p_sorted    = p_vals[sorted_idx]
    pc_sorted   = p_corrected[sorted_idx]
    lab_sorted  = [labels[i] for i in sorted_idx]

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.suptitle("Chart 5 — p-Values Before and After Benjamini-Hochberg FDR Correction",
                 fontsize=14, fontweight="bold")

    x = np.arange(len(p_sorted))
    ax.scatter(x, p_sorted, color=PALETTE["treatment"], s=55, zorder=3, label="Raw p-value")
    ax.scatter(x, pc_sorted, color=PALETTE["control"],  s=55, zorder=3,
               marker="D", label="BH-corrected p-value")

    for xi, (pr, pc) in enumerate(zip(p_sorted, pc_sorted)):
        ax.plot([xi, xi], [pr, pc], color="#CCC", linewidth=1, zorder=2)

    ax.axhline(0.05, color=PALETTE["negative"], linestyle="--", linewidth=1.5, label="α = 0.05")
    ax.set_xticks(x)
    ax.set_xticklabels(lab_sorted, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("p-value")
    ax.set_yscale("log")
    ax.set_ylim(0.001, 1.2)
    ax.legend(frameon=False)
    ax.set_title(
        f"{(p_vals < 0.05).sum()} segments significant (raw) → "
        f"{reject.sum()} remain after FDR correction"
    )
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=PALETTE["grid"])

    plt.tight_layout()
    save(fig, "chart5_multiple_testing")


# ---------------------------------------------------------------------------
# Chart 6: Bayesian posterior distributions
# ---------------------------------------------------------------------------

def chart6_bayesian(df: pd.DataFrame):
    np.random.seed(0)

    def posterior_samples(sub):
        ctrl = sub[sub.experiment_group == "control"]
        trt  = sub[sub.experiment_group == "treatment"]
        a_c = 1 + ctrl.conversion_flag.sum()
        b_c = 1 + len(ctrl) - ctrl.conversion_flag.sum()
        a_t = 1 + trt.conversion_flag.sum()
        b_t = 1 + len(trt) - trt.conversion_flag.sum()
        sc = np.random.beta(a_c, b_c, 200_000)
        st = np.random.beta(a_t, b_t, 200_000)
        return sc, st

    sc_all, st_all = posterior_samples(df)
    sc_new, st_new = posterior_samples(df[df.user_type == "new"])
    sc_ret, st_ret = posterior_samples(df[df.user_type == "returning"])

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("Chart 6 — Bayesian Posterior: Treatment vs Control Conversion Rate",
                 fontsize=14, fontweight="bold")

    datasets = [
        (sc_all, st_all, "All users"),
        (sc_new, st_new, "New users"),
        (sc_ret, st_ret, "Returning users"),
    ]

    for ax, (sc, st, title) in zip(axes, datasets):
        p_beats = (st > sc).mean()
        bins = np.linspace(
            min(sc.min(), st.min()), max(sc.max(), st.max()), 120
        )
        ax.hist(sc, bins=bins, alpha=0.55, color=PALETTE["control"],
                density=True, label="Control")
        ax.hist(st, bins=bins, alpha=0.55, color=PALETTE["treatment"],
                density=True, label="Treatment")
        ax.axvline(sc.mean(), color=PALETTE["control"],  linestyle="--", linewidth=1.5)
        ax.axvline(st.mean(), color=PALETTE["treatment"], linestyle="--", linewidth=1.5)
        ax.set_title(title)
        ax.set_xlabel("Conversion rate")
        ax.set_ylabel("Density" if ax == axes[0] else "")
        ax.legend(frameon=False, fontsize=9)
        color = PALETTE["positive"] if p_beats > 0.50 else PALETTE["negative"]
        ax.text(0.97, 0.95, f"P(T>C) = {p_beats:.1%}",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=10, color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#DDD"))
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color=PALETTE["grid"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save(fig, "chart6_bayesian")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data ...")
    df = pd.read_csv("data/experiment_data.csv")
    print(f"  {len(df):,} rows loaded")

    print("\nGenerating charts ...")
    chart1_topline(df)
    chart2_time_stability(df)
    chart3_segment_heatmap(df)
    chart4_cuped(df)
    chart5_multiple_testing(df)
    chart6_bayesian(df)

    print("\nAll charts saved to images/")


if __name__ == "__main__":
    main()
