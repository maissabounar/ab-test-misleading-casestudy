# Signup Flow A/B Test: +5% Conversion Lift, Negative Net Impact

A subscription app tested a simplified onboarding flow. Variant B removed one step and surfaced a promotional annual plan earlier. Two weeks, 120,000 users, conversion up 5.1%.

The team was ready to ship. The data says no.

---

## Impact on the business

A 5% lift at scale feels decisive. Here it was covering a 58% spike in refund rate, a 7.9% CVR drop for returning users, and revenue per user down 4.6%.

None of that was visible in the headline number. This is what the deeper cut found.

---

## Executive Summary

| Metric | Control | Treatment | Delta |
|---|---|---|---|
| Conversion rate | 14.8% | 15.6% | +5.1% |
| CUPED-adjusted uplift | | | +3.4% |
| Refund rate | 3.1% | 4.9% | +58% |
| Revenue per user | $6.72 | $6.41 | -4.6% |
| Returning user CVR | 24.2% | 22.3% | -7.9% |
| Mobile Safari CVR delta | | | -4.1% |

The conversion gain is real but narrow. It comes from new users, runs on paid social traffic, and decays after 48 hours. Returning users convert worse. Revenue per user is down. Refund rate is up 58%.


> [!IMPORTANT]
>**Recommendation: Do not ship globally.** A restricted rollout to new users on Chrome and desktop is defensible once the Safari issue is diagnosed. Everything else needs more data.


![Conversion rate by group with 95% CI](images/chart1_topline_uplift.png)

---

## Experiment Setup

**Product:** Subscription app onboarding and checkout flow

**Variant:** Removed one onboarding step. Promotional annual plan surfaced earlier in the funnel.

**Hypothesis:** Less friction increases conversion. Surfacing the annual plan earlier captures users while intent is high.

**Duration:** 14 days / **Sample:** 120,000 users, 50/50 split

**Primary metric:** Conversion rate

**Guardrail metrics:** Refund rate, revenue per user, revenue per converter

**CUPED covariate:** `pre_experiment_activity_score` (pre-enrollment activity, correlated with conversion propensity)

| Field | Description |
|---|---|
| `experiment_group` | control / treatment |
| `conversion_flag` | 1 if converted |
| `revenue` | Revenue at user level |
| `refund_flag` | 1 if refund issued |
| `device_type` | mobile / desktop |
| `browser` | chrome_mobile, safari_mobile, chrome_desktop, firefox, edge |
| `country` | US, UK, CA, AU, DE, FR, BR, MX, IN, other |
| `user_type` | new / returning |
| `traffic_source` | organic, paid_search, paid_social, email, direct |
| `pre_experiment_activity_score` | Pre-enrollment activity score, used as CUPED covariate |
| `prior_conversion_propensity` | Pre-experiment conversion estimate |
| `day_since_launch` | Enrollment day (1 to 14) |

---

## Top-Line Result

```
Control   n=60,012   CVR=14.80%
Treatment n=59,988   CVR=15.56%

Absolute uplift:  +0.76 pp
Relative uplift:  +5.1%
z-statistic:       6.21
p-value:          <0.001
95% CI:           [+0.52 pp, +1.00 pp]
```

Significant, tight CI, clean split. If this were the only cut, it would ship.

---

## What Broke Under the Surface

### 1. Baseline imbalance inflates the raw uplift

Treatment had slightly higher pre-experiment activity scores than control. CUPED regresses out `pre_experiment_activity_score` to remove that pre-existing difference from the effect estimate.

```
Raw uplift:            +0.76 pp  (+5.1%)
CUPED-adjusted uplift: +0.50 pp  (+3.4%)
Adjusted 95% CI:       [+0.28 pp, +0.72 pp]
Variance reduction:     14.8%
```

A third of the apparent effect is baseline imbalance, not treatment. The adjusted number is still significant, but it shifts the revenue case considerably.

The bars below show raw vs adjusted with 95% CI. The gap is not marginal.

![Raw vs CUPED-adjusted uplift](images/chart4_cuped.png)

---

### 2. The effect decays fast

| Day | Control CVR | Treatment CVR | Relative Uplift | CI crosses zero |
|---|---|---|---|---|
| 1 | 15.3% | 16.7% | +9.2% | No |
| 2 | 15.1% | 16.3% | +7.9% | No |
| 3 | 14.9% | 15.6% | +4.7% | No |
| 4 | 14.8% | 15.4% | +4.1% | No |
| 5 | 14.7% | 15.2% | +3.4% | No |
| 7 | 14.6% | 14.9% | +2.1% | Borderline |
| 10 | 14.5% | 14.7% | +1.4% | Yes |
| 14 | 14.4% | 14.5% | +0.7% | Yes |

Days 1 and 2 are propping up the aggregate. This is likely users who were close to converting anyway, responding quickly to the promo framing. By day 10 the CI crosses zero. By day 14 there is essentially nothing left.

The +5.1% is a weighted average built on the first 48 hours. We don't know yet whether steady-state effect would land above or below 2%, but it's not 5%.

![Daily relative uplift with CI bands](images/chart2_time_stability.png)

---

### 3. New and returning users are having opposite experiences

| Segment | Control CVR | Treatment CVR | Relative Uplift | p (raw) | p (BH) | Ship |
|---|---|---|---|---|---|---|
| new | 12.5% | 14.4% | +15.2% | <0.001 | <0.001 | Yes |
| returning | 24.2% | 22.3% | -7.9% | <0.001 | <0.001 | No |

The aggregate lift is entirely new users. Returning users are converting worse, significantly so after FDR correction, and they represent 30% of the base. The promotional framing likely feels misaligned to someone who already knows the product.

**Browser:**

| Segment | Control CVR | Treatment CVR | Relative Uplift | p (BH) | Ship |
|---|---|---|---|---|---|
| chrome_desktop | 16.2% | 18.7% | +15.4% | <0.001 | Yes |
| chrome_mobile | 13.8% | 14.9% | +8.0% | <0.001 | Yes |
| safari_mobile | 14.0% | 13.4% | -4.3% | 0.031 | No |
| firefox | 15.1% | 15.3% | +1.3% | 0.54 | No |

Something is off on mobile Safari. Could be a rendering issue, a timing problem, or the new step not loading cleanly. We don't know yet. It needs an eng ticket before we consider widening.

**Traffic source:**

| Segment | Relative Uplift | BH significant |
|---|---|---|
| paid_social | +14.2% | Yes |
| email | +6.1% | Yes |
| paid_search | +3.8% | Yes |
| organic | +1.2% | No |
| direct | -0.9% | No |

Most of the lift is paid social. These users arrive already in purchase mode and respond to the promo framing. Organic and direct do not. This could be driven partly by different price sensitivity across acquisition channels, but the gap is worth watching in the next run.

![Segment uplift heatmap](images/chart3_segment_heatmap.png)

---

### 4. Several segment wins were noise

14 segment cuts at α = 0.05 without correction. Benjamini-Hochberg FDR applied:

```
Segments tested:           14
Significant (raw p<0.05):   9
Significant (BH-corrected): 5
```

Germany and Brazil both showed positive effects at p ≈ 0.03. Neither survived correction. Without FDR those would have been in the ship argument.

![p-values before and after BH correction](images/chart5_multiple_testing.png)

---

### 5. Bayesian read: new users yes, returning users no

Beta-Binomial model, Beta(1,1) prior, 200,000 posterior samples.

| Cohort | P(T > C) | P(uplift > +2%) | P(T < C) |
|---|---|---|---|
| All users | 99.1% | 74.3% | 0.9% |
| New users only | 99.8% | 91.2% | 0.2% |
| Returning users only | 0.7% | 0.1% | 99.3% |

99.3% probability the variant hurts returning users. That is not a marginal call.

![Posterior distributions: all users, new users, returning users](images/chart6_bayesian.png)

---

### 6. Guardrail metrics are moving the wrong way

| Metric | Control | Treatment | Delta |
|---|---|---|---|
| Conversion rate | 14.80% | 15.56% | +5.1% |
| Refund rate (all users) | 3.1% | 4.9% | +58.1% |
| Refund rate (converters) | 20.9% | 31.5% | +50.7% |
| Revenue per user | $6.72 | $6.41 | -4.6% |
| Revenue per converter | $45.40 | $41.20 | -9.3% |

The promo plan is pulling in users who churn fast. Revenue per converter is down 9.3%. We are buying conversions and a third of them refund. Revenue per user is negative despite the lift.

---

## Decision

This is a recommendation against a global ship, not a kill decision.

What we know: returning users are measurably worse off, the effect decays sharply after day 2, revenue quality is degrading, and the Safari segment is broken. All of that is significant and directionally consistent.

What we're assuming: that the retention impact beyond this 14-day window is negative, that steady-state effect is below 2%, and that the Safari issue is fixable. None of that is confirmed yet.

Given what we can see, the risk of shipping globally is not worth the upside. The conversion gain for new users on Chrome is real and worth pursuing. The rest needs more time.

**Path forward:**

Segment to new users only, exclude returning users entirely. Get an eng investigation on mobile Safari before widening. Reset the success bar to +2% CUPED-adjusted, not raw conversion. Add refund rate and 30-day retention as co-primary metrics, not afterthought guardrails. Run for four full weeks.

---

## What I'd Tell the PM

The +5% won't be there in 30 days. It's front-loaded on the first 48 hours and it fades. If we ship this globally and look back in a month, the number will be smaller and the refund rate story will be harder to explain.

We're buying conversions with a promo offer. That's not always bad, but here a third of those converters are refunding. Revenue per user is already down 4.6% in a two-week window. That compounds.

Returning users are a hard no. 7.9% CVR drop, holds after correction, 30% of the base. We don't know yet what that means for 60-day retention, but I wouldn't ship this to that group until we do.

Safari needs an eng ticket. Could be a rendering bug, could be something structural with the new step. We genuinely don't know, and shipping to that segment without knowing is a risk we don't have to take.

Honest read: Chrome plus new users only, rerun for four weeks with refund rate as a primary metric. If CUPED-adjusted uplift holds above 2% and the refund rate stabilises, the case for a broader rollout becomes a real conversation.

---

## Business Impact

500,000 monthly eligible users.

| Scenario | Incremental Conversions | Gross Revenue | Refund Cost | Net Revenue |
|---|---|---|---|---|
| Ship globally | +3,800 | +$156,600 | -$52,400 | +$104,200 |
| New users only | +2,950 | +$121,400 | -$18,700 | +$102,700 |
| No ship | 0 | $0 | $0 | $0 |

Net revenue gap between global and restricted launch is $1,500 a month. The refund cost difference is $33,700. The returning-user retention risk in the global scenario is not in these numbers.

---

## Repo Contents

```
ab-test-misleading-casestudy/
├── README.md
├── requirements.txt
├── data/                          # generated by python/generate_data.py
│   ├── experiment_data.csv
│   ├── time_stability.csv
│   └── segment_results.csv
├── images/                        # generated by python/generate_charts.py
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
| `python/generate_data.py` | Synthetic dataset with segment-level heterogeneity, time decay, refund uplift, and false-positive segments baked into the DGP |
| `python/experiment_analysis.py` | z-test, CUPED, time stability, segment analysis, BH correction, Bayesian Beta-Binomial, guardrail metrics, business impact |
| `python/generate_charts.py` | Six charts |
| `sql/01_experiment_summary.sql` | Top-line CVR, uplift, z-test, 95% CI in BigQuery |
| `sql/02_segment_analysis.sql` | Segment-level uplift across all dimensions in one query |
| `sql/03_guardrail_metrics.sql` | Refund rate, revenue per user, revenue per converter, net revenue |
| `sql/04_time_stability.sql` | Daily CVR, uplift, and CI bounds |

---

## Reproducing the Analysis

```bash
git clone https://github.com/maissabounar/ab-test-misleading-casestudy
cd ab-test-misleading-casestudy
pip install -r requirements.txt

python python/generate_data.py
python python/experiment_analysis.py
python python/generate_charts.py
```
