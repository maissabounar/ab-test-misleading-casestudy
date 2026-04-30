"""
Generates synthetic experiment dataset for the A/B test case study.
120K users, realistic segment-level treatment heterogeneity, guardrail metric degradation.
Outputs: data/experiment_data.csv
"""

import os

import numpy as np
import pandas as pd

np.random.seed(42)
N = 120_000


def _assign_user_attributes(n):
    user_type = np.random.choice(["new", "returning"], size=n, p=[0.70, 0.30])

    device_type = np.where(np.random.random(n) < 0.52, "mobile", "desktop")

    browser = np.empty(n, dtype=object)
    for i in range(n):
        if device_type[i] == "mobile":
            browser[i] = np.random.choice(
                ["chrome_mobile", "safari_mobile", "other_mobile"],
                p=[0.50, 0.36, 0.14],
            )
        else:
            browser[i] = np.random.choice(
                ["chrome_desktop", "firefox", "edge", "safari_desktop", "other_desktop"],
                p=[0.52, 0.18, 0.14, 0.10, 0.06],
            )

    country = np.random.choice(
        ["US", "UK", "CA", "AU", "DE", "FR", "BR", "MX", "IN", "other"],
        size=n,
        p=[0.38, 0.14, 0.09, 0.07, 0.07, 0.06, 0.05, 0.04, 0.04, 0.06],
    )

    traffic_source = np.random.choice(
        ["organic", "paid_search", "paid_social", "email", "direct"],
        size=n,
        p=[0.34, 0.24, 0.21, 0.12, 0.09],
    )

    return user_type, device_type, browser, country, traffic_source


def _base_conversion_prob(user_type, device_type, browser, traffic_source):
    prob = np.full(len(user_type), 0.118)

    prob[user_type == "returning"] *= 2.05
    prob[device_type == "desktop"] *= 1.12

    prob[browser == "safari_mobile"] *= 0.94
    prob[browser == "chrome_desktop"] *= 1.06

    prob[traffic_source == "email"] *= 1.28
    prob[traffic_source == "paid_social"] *= 1.18
    prob[traffic_source == "paid_search"] *= 1.10
    prob[traffic_source == "direct"] *= 1.05

    noise = np.random.normal(0, 0.008, len(prob))
    return np.clip(prob + noise, 0.02, 0.70)


def _treatment_lift(user_type, browser, day_since_launch):
    lift = np.zeros(len(user_type))

    lift[user_type == "new"] = 0.020
    lift[user_type == "returning"] = -0.019

    safari_mask = browser == "safari_mobile"
    lift[safari_mask] *= 0.45
    lift[(browser == "chrome_mobile") & (user_type == "new")] *= 1.08

    day_decay = np.ones(len(day_since_launch))
    day_decay[(day_since_launch >= 3) & (day_since_launch <= 5)] = 0.62
    day_decay[day_since_launch >= 6] = 0.30

    lift *= day_decay
    lift += np.random.normal(0, 0.004, len(lift))

    return lift


def _prior_propensity(user_type, traffic_source, device_type):
    base = np.where(user_type == "returning", 0.24, 0.12)
    base += np.where(traffic_source == "email", 0.03, 0.0)
    base += np.where(device_type == "desktop", 0.01, -0.005)
    base += np.random.beta(1.2, 8, len(user_type)) * 0.08

    return np.clip(base, 0.01, 0.80)


def generate():
    print(f"Generating {N:,} users ...")

    experiment_group = np.where(np.random.random(N) < 0.50, "control", "treatment")
    is_treatment = experiment_group == "treatment"

    user_type, device_type, browser, country, traffic_source = _assign_user_attributes(N)

    day_probs = np.array([
        0.12, 0.11, 0.09, 0.09, 0.08,
        0.08, 0.07, 0.07, 0.07, 0.06,
        0.06, 0.05, 0.05, 0.05,
    ])
    day_probs = day_probs / day_probs.sum()

    day_since_launch = np.random.choice(
        range(1, 15),
        size=N,
        p=day_probs,
    )

    prior_conversion_propensity = _prior_propensity(user_type, traffic_source, device_type)

    pre_experiment_activity_score = (
        prior_conversion_propensity * 100 + np.random.normal(0, 8, N)
    ).clip(0, 100)

    prior_sessions = np.round(
        np.where(
            user_type == "returning",
            np.random.exponential(12, N),
            np.random.exponential(1.8, N),
        )
    ).astype(int)
    prior_sessions = prior_sessions.clip(0, 150)

    session_count_7d = np.round(np.random.exponential(3.2, N)).astype(int).clip(1, 40)

    variant_exposure_count = np.where(
        is_treatment,
        np.random.choice([1, 2, 3], size=N, p=[0.74, 0.18, 0.08]),
        1,
    )

    base_prob = _base_conversion_prob(user_type, device_type, browser, traffic_source)
    lift = np.where(is_treatment, _treatment_lift(user_type, browser, day_since_launch), 0.0)

    conversion_prob = np.clip(base_prob + lift, 0.01, 0.95)
    conversion_flag = (np.random.random(N) < conversion_prob).astype(int)

    base_revenue = np.where(
        conversion_flag == 1,
        np.where(
            is_treatment,
            np.random.normal(41.5, 14.0, N),
            np.random.normal(45.2, 13.5, N),
        ),
        0.0,
    )
    revenue = np.maximum(base_revenue * conversion_flag, 0.0).round(2)

    base_refund_prob = np.where(is_treatment, 0.049, 0.031)
    refund_flag = np.where(
        conversion_flag == 1,
        (np.random.random(N) < base_refund_prob).astype(int),
        0,
    )

    start_ts = pd.Timestamp("2024-10-01")
    assignment_timestamp = (
        start_ts
        + pd.to_timedelta((day_since_launch - 1).astype(int), unit="D")
        + pd.to_timedelta(np.random.randint(0, 86_400, N), unit="s")
    )

    df = pd.DataFrame(
        {
            "user_id": [f"u_{i:07d}" for i in range(N)],
            "experiment_group": experiment_group,
            "assignment_timestamp": assignment_timestamp,
            "conversion_flag": conversion_flag,
            "revenue": revenue,
            "refund_flag": refund_flag,
            "device_type": device_type,
            "browser": browser,
            "country": country,
            "user_type": user_type,
            "traffic_source": traffic_source,
            "prior_sessions": prior_sessions,
            "prior_conversion_propensity": prior_conversion_propensity.round(4),
            "pre_experiment_activity_score": pre_experiment_activity_score.round(2),
            "session_count_7d": session_count_7d,
            "variant_exposure_count": variant_exposure_count,
            "day_since_launch": day_since_launch,
        }
    )

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/experiment_data.csv", index=False)

    print(f"Saved {len(df):,} rows to data/experiment_data.csv")

    ctrl = df[df["experiment_group"] == "control"]
    trt = df[df["experiment_group"] == "treatment"]

    print(f"\nControl   n={len(ctrl):,}  CVR={ctrl.conversion_flag.mean():.3%}")
    print(f"Treatment n={len(trt):,}  CVR={trt.conversion_flag.mean():.3%}")

    uplift = trt.conversion_flag.mean() / ctrl.conversion_flag.mean() - 1
    print(f"Relative uplift: {uplift:+.1%}")
    print(
        f"Refund rate  control={ctrl.refund_flag.mean():.3%}  "
        f"treatment={trt.refund_flag.mean():.3%}"
    )


if __name__ == "__main__":
    generate()