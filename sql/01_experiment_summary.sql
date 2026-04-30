-- =============================================================================
-- 01_experiment_summary.sql
-- Top-line experiment result: sample size, conversion rate, uplift, z-test.
-- Dialect: BigQuery Standard SQL
-- =============================================================================

WITH base AS (
  SELECT
    experiment_group,
    COUNT(DISTINCT user_id)                                   AS n_users,
    SUM(conversion_flag)                                      AS conversions,
    SAFE_DIVIDE(SUM(conversion_flag), COUNT(DISTINCT user_id)) AS conversion_rate,
    AVG(revenue)                                              AS revenue_per_user,
    SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(conversion_flag), 0)) AS revenue_per_converter,
    AVG(refund_flag)                                          AS refund_rate
  FROM `project.dataset.experiment_data`
  WHERE experiment_group IN ('control', 'treatment')
  GROUP BY 1
),

pivot AS (
  SELECT
    MAX(IF(experiment_group = 'control',   n_users,           NULL)) AS n_control,
    MAX(IF(experiment_group = 'treatment', n_users,           NULL)) AS n_treatment,
    MAX(IF(experiment_group = 'control',   conversions,       NULL)) AS conv_control,
    MAX(IF(experiment_group = 'treatment', conversions,       NULL)) AS conv_treatment,
    MAX(IF(experiment_group = 'control',   conversion_rate,   NULL)) AS cvr_control,
    MAX(IF(experiment_group = 'treatment', conversion_rate,   NULL)) AS cvr_treatment,
    MAX(IF(experiment_group = 'control',   revenue_per_user,  NULL)) AS rev_per_user_control,
    MAX(IF(experiment_group = 'treatment', revenue_per_user,  NULL)) AS rev_per_user_treatment,
    MAX(IF(experiment_group = 'control',   refund_rate,       NULL)) AS refund_rate_control,
    MAX(IF(experiment_group = 'treatment', refund_rate,       NULL)) AS refund_rate_treatment
  FROM base
)

SELECT
  n_control,
  n_treatment,
  conv_control,
  conv_treatment,
  ROUND(cvr_control  * 100, 3)                                AS cvr_control_pct,
  ROUND(cvr_treatment * 100, 3)                               AS cvr_treatment_pct,
  ROUND((cvr_treatment - cvr_control) * 100, 4)               AS abs_uplift_pp,
  ROUND(SAFE_DIVIDE(cvr_treatment - cvr_control, cvr_control) * 100, 2) AS rel_uplift_pct,

  -- Pooled z-test components (BigQuery does not have a built-in prop-test)
  ROUND(
    SAFE_DIVIDE(
      cvr_treatment - cvr_control,
      SQRT(
        (cvr_control * (1 - cvr_control) / n_control)
        + (cvr_treatment * (1 - cvr_treatment) / n_treatment)
      )
    ), 4
  ) AS z_statistic,

  -- 95% confidence interval on absolute difference
  ROUND(
    (cvr_treatment - cvr_control)
    - 1.96 * SQRT(
        (cvr_control * (1 - cvr_control) / n_control)
        + (cvr_treatment * (1 - cvr_treatment) / n_treatment)
      ), 4
  ) AS ci_lower_pp,

  ROUND(
    (cvr_treatment - cvr_control)
    + 1.96 * SQRT(
        (cvr_control * (1 - cvr_control) / n_control)
        + (cvr_treatment * (1 - cvr_treatment) / n_treatment)
      ), 4
  ) AS ci_upper_pp,

  ROUND(rev_per_user_control,   2) AS rev_per_user_control,
  ROUND(rev_per_user_treatment, 2) AS rev_per_user_treatment,
  ROUND(SAFE_DIVIDE(rev_per_user_treatment - rev_per_user_control, rev_per_user_control) * 100, 2)
    AS rev_per_user_delta_pct,

  ROUND(refund_rate_control   * 100, 3) AS refund_rate_control_pct,
  ROUND(refund_rate_treatment * 100, 3) AS refund_rate_treatment_pct,
  ROUND(SAFE_DIVIDE(refund_rate_treatment - refund_rate_control, refund_rate_control) * 100, 2)
    AS refund_rate_delta_pct

FROM pivot;
