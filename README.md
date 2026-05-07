# Signup Flow A/B Test: +5% Conversion Lift, Negative Net Impact

A subscription app tested a simplified onboarding flow.

Variant B removed one onboarding step and showed the annual promo plan earlier.

After 14 days and 120000 users, conversion was up 5.1%.

The team was ready to ship.

The deeper analysis said no.

---

## Executive Summary

| Metric | Control | Treatment | Delta |
|---|---:|---:|---:|
| Conversion rate | 14.8% | 15.6% | +5.1% |
| CUPED-adjusted uplift |  |  | +3.4% |
| Refund rate | 3.1% | 4.9% | +58% |
| Revenue per user | $6.72 | $6.41 | -4.6% |
| Returning user CVR | 24.2% | 22.3% | -7.9% |
| Mobile Safari CVR delta |  |  | -4.1% |

The topline lift is statistically significant, but not healthy.

It is concentrated in new users, Chrome traffic, and paid social. Returning users convert worse. Refunds increase. Revenue per user drops.

> [!IMPORTANT]
> Recommendation: do not ship globally.
>
> Ship only to new users after excluding mobile Safari and validating refund impact over a longer window.

![Conversion rate by group with 95% CI](images/chart1_topline_uplift.png)

---

## Experiment Setup

| Item | Detail |
|---|---|
| Product area | Subscription app onboarding and checkout |
| Variant | Removed one onboarding step and surfaced annual promo earlier |
| Hypothesis | Less friction increases conversion |
| Duration | 14 days |
| Sample | 120000 users |
| Split | 50 / 50 |
| Primary metric | Conversion rate |
| Guardrails | Refund rate, revenue per user, revenue per converter |
| CUPED covariate | `pre_experiment_activity_score` |

### Dataset

| Field | Description |
|---|---|
| `experiment_group` | control / treatment |
| `conversion_flag` | 1 if user converted |
| `revenue` | User-level revenue |
| `refund_flag` | 1 if refund issued |
| `device_type` | mobile / desktop |
| `browser` | chrome_mobile, safari_mobile, chrome_desktop, firefox, edge |
| `country` | US, UK, CA, AU, DE, FR, BR, MX, IN, other |
| `user_type` | new / returning |
| `traffic_source` | organic, paid_search, paid_social, email, direct |
| `pre_experiment_activity_score` | Pre-enrollment activity score used for CUPED |
| `prior_conversion_propensity` | Pre-experiment conversion estimate |
| `day_since_launch` | Enrollment day, from 1 to 14 |

---

## Topline Result

```text
Control     n=60012   CVR=14.80%
Treatment   n=59988   CVR=15.56%

Absolute uplift:   +0.76 pp
Relative uplift:   +5.1%
z-statistic:        6.21
p-value:           <0.001
95% CI:            [+0.52 pp, +1.00 pp]
```

The test passes on conversion rate.

That is where the simple read ends.

---

## What Changed the Decision

### 1. CUPED reduced the uplift

Treatment users entered the experiment with slightly higher pre-experiment activity.

CUPED adjusts for this baseline imbalance.

```text
Raw uplift:             +0.76 pp  (+5.1%)
CUPED-adjusted uplift:  +0.50 pp  (+3.4%)
Adjusted 95% CI:        [+0.28 pp, +0.72 pp]
Variance reduction:      14.8%
```

The lift remains positive, but the business case becomes weaker.

![Raw vs CUPED-adjusted uplift](images/chart4_cuped.png)

---

### 2. The effect faded after 48 hours

| Day | Control CVR | Treatment CVR | Relative Uplift | CI crosses zero |
|---:|---:|---:|---:|---|
| 1 | 15.3% | 16.7% | +9.2% | No |
| 2 | 15.1% | 16.3% | +7.9% | No |
| 3 | 14.9% | 15.6% | +4.7% | No |
| 4 | 14.8% | 15.4% | +4.1% | No |
| 5 | 14.7% | 15.2% | +3.4% | No |
| 7 | 14.6% | 14.9% | +2.1% | Borderline |
| 10 | 14.5% | 14.7% | +1.4% | Yes |
| 14 | 14.4% | 14.5% | +0.7% | Yes |

The aggregate result is carried by days 1 and 2.

By day 10, the effect is no longer reliable. This points to short-term promo pull, not stable funnel improvement.

![Daily relative uplift with CI bands](images/chart2_time_stability.png)

---

### 3. New users won, returning users lost

| Segment | Control CVR | Treatment CVR | Relative Uplift | p raw | p BH | Decision |
|---|---:|---:|---:|---:|---:|---|
| new | 12.5% | 14.4% | +15.2% | <0.001 | <0.001 | Ship |
| returning | 24.2% | 22.3% | -7.9% | <0.001 | <0.001 | Do not ship |

The variant works for new users.

It hurts returning users, who represent 30% of the base.

The same promo framing does not fit both audiences.

### Browser split

| Browser | Control CVR | Treatment CVR | Relative Uplift | p BH | Decision |
|---|---:|---:|---:|---:|---|
| chrome_desktop | 16.2% | 18.7% | +15.4% | <0.001 | Ship |
| chrome_mobile | 13.8% | 14.9% | +8.0% | <0.001 | Ship |
| safari_mobile | 14.0% | 13.4% | -4.3% | 0.031 | Do not ship |
| firefox | 15.1% | 15.3% | +1.3% | 0.54 | Do not ship |

Mobile Safari needs engineering investigation before rollout.

### Traffic source split

| Traffic source | Relative Uplift | BH significant |
|---|---:|---|
| paid_social | +14.2% | Yes |
| email | +6.1% | Yes |
| paid_search | +3.8% | Yes |
| organic | +1.2% | No |
| direct | -0.9% | No |

Paid social drives most of the lift. Organic and direct do not show a reliable gain.

![Segment uplift heatmap](images/chart3_segment_heatmap.png)

---

### 4. Some segment wins were false positives

14 segment cuts were tested.

```text
Segments tested:             14
Significant before FDR:       9
Significant after FDR:        5
```

Germany and Brazil looked positive before correction.

Neither survived Benjamini-Hochberg FDR correction.

![p-values before and after BH correction](images/chart5_multiple_testing.png)

---

### 5. Bayesian analysis confirmed the risk

Beta-Binomial model with Beta(1,1) prior and 200000 posterior samples.

| Cohort | P(Treatment > Control) | P(uplift > +2%) | P(Treatment < Control) |
|---|---:|---:|---:|
| All users | 99.1% | 74.3% | 0.9% |
| New users | 99.8% | 91.2% | 0.2% |
| Returning users | 0.7% | 0.1% | 99.3% |

There is a 99.3% probability that Variant B hurts returning users.

![Posterior distributions: all users, new users, returning users](images/chart6_bayesian.png)

---

### 6. Guardrails failed

| Metric | Control | Treatment | Delta |
|---|---:|---:|---:|
| Conversion rate | 14.80% | 15.56% | +5.1% |
| Refund rate, all users | 3.1% | 4.9% | +58.1% |
| Refund rate, converters | 20.9% | 31.5% | +50.7% |
| Revenue per user | $6.72 | $6.41 | -4.6% |
| Revenue per converter | $45.40 | $41.20 | -9.3% |

Variant B creates more conversions, but lower-quality conversions.

Refunds rise. Revenue per converter falls. Revenue per user turns negative despite the lift.

---

## Decision

Do not ship Variant B globally.

The test shows a real opportunity, but only in specific segments.

### Recommended rollout

| Audience | Decision |
|---|---|
| New users on Chrome | Roll out carefully |
| Returning users | Keep control |
| Mobile Safari | Exclude until fixed |
| Organic and direct traffic | Keep monitoring |
| Paid social | Strongest candidate for rollout |

### Next test

- Run for 4 full weeks
- Use CUPED-adjusted uplift as the success metric
- Set the success threshold at +2% adjusted uplift
- Add refund rate as a decision metric
- Add 30-day retention as a decision metric
- Keep a holdout for returning users

---

## Business Impact Estimate

Assumption: 500000 monthly eligible users.

| Scenario | Incremental Conversions | Gross Revenue | Refund Cost | Net Revenue |
|---|---:|---:|---:|---:|
| Ship globally | +3800 | +$156600 | -$52400 | +$104200 |
| New users only | +2950 | +$121400 | -$18700 | +$102700 |
| No ship | 0 | $0 | $0 | $0 |

Global rollout adds only $1500 more net revenue than restricted rollout.

It also adds $33700 in refund cost and exposes returning users to a worse experience.

Restricted rollout keeps most of the upside with much lower risk.

---

## Repo Contents

```text
ab-test-misleading-casestudy/
├── README.md
├── requirements.txt
├── data/
│   ├── experiment_data.csv
│   ├── time_stability.csv
│   └── segment_results.csv
├── images/
│   ├── chart1_topline_uplift.png
│   ├── chart2_time_stability.png
│   ├── chart3_segment_heatmap.png
│   ├── chart4_cuped.png
│   ├── chart5_multiple_testing.png
│   └── chart6_bayesian.png
├── sql/
│   ├── 01_experiment_summary.sql
│   ├── 02_segment_analysis.sql
│   ├── 03_guardrail_metrics.sql
│   └── 04_time_stability.sql
└── python/
    ├── generate_data.py
    ├── experiment_analysis.py
    └── generate_charts.py
```

---

## Code Overview

| File | Purpose |
|---|---|
| `python/generate_data.py` | Generates synthetic experiment data with segment heterogeneity, time decay, refund pressure, and false-positive segments |
| `python/experiment_analysis.py` | Runs z-test, CUPED, segment analysis, FDR correction, Bayesian analysis, guardrail checks, and business impact estimate |
| `python/generate_charts.py` | Generates the six charts used in the README |
| `sql/01_experiment_summary.sql` | Calculates topline conversion rate, uplift, z-test, and 95% CI in BigQuery |
| `sql/02_segment_analysis.sql` | Calculates segment-level uplift across user, browser, country, device, and traffic dimensions |
| `sql/03_guardrail_metrics.sql` | Calculates refund rate, revenue per user, revenue per converter, and net revenue |
| `sql/04_time_stability.sql` | Calculates daily conversion rate, uplift, and confidence bounds |

---

## Methods used

- A/B test analysis
- Statistical significance testing
- CUPED adjustment
- Segment analysis
- Multiple testing correction
- Bayesian interpretation
- Revenue and refund guardrails
- Business impact estimation
- Product decision framing

The key point: conversion went up, but the product decision was still no.
