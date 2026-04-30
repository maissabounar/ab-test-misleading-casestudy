-- =============================================================================
-- 04_time_stability.sql
-- Daily conversion rate and uplift by experiment group.
-- Surfaces the treatment effect decay after day 2.
-- Dialect: BigQuery Standard SQL
-- =============================================================================

WITH daily AS (
  SELECT
    day_since_launch,
    experiment_group,
    COUNT(DISTINCT user_id)                                      AS n_users,
    SUM(conversion_flag)                                         AS conversions,
    SAFE_DIVIDE(SUM(conversion_flag), COUNT(DISTINCT user_id))   AS cvr
  FROM `project.dataset.experiment_data`
  GROUP BY 1, 2
),

pivoted AS (
  SELECT
    day_since_launch,
    MAX(IF(experiment_group = 'control',   n_users,     NULL)) AS n_control,
    MAX(IF(experiment_group = 'treatment', n_users,     NULL)) AS n_treatment,
    MAX(IF(experiment_group = 'control',   conversions, NULL)) AS conv_control,
    MAX(IF(experiment_group = 'treatment', conversions, NULL)) AS conv_treatment,
    MAX(IF(experiment_group = 'control',   cvr,         NULL)) AS cvr_control,
    MAX(IF(experiment_group = 'treatment', cvr,         NULL)) AS cvr_treatment
  FROM daily
  GROUP BY 1
),

with_stats AS (
  SELECT
    *,
    ROUND((cvr_treatment - cvr_control) * 100, 4)               AS abs_uplift_pp,
    ROUND(
      SAFE_DIVIDE(cvr_treatment - cvr_control, cvr_control) * 100, 2
    )                                                            AS rel_uplift_pct,

    -- z-statistic
    ROUND(
      SAFE_DIVIDE(
        cvr_treatment - cvr_control,
        SQRT(
          SAFE_DIVIDE(cvr_control * (1 - cvr_control), n_control)
          + SAFE_DIVIDE(cvr_treatment * (1 - cvr_treatment), n_treatment)
        )
      ), 4
    )                                                            AS z_statistic,

    -- 95% CI bounds on absolute difference
    ROUND(
      (cvr_treatment - cvr_control)
      - 1.96 * SQRT(
          SAFE_DIVIDE(cvr_control * (1 - cvr_control), n_control)
          + SAFE_DIVIDE(cvr_treatment * (1 - cvr_treatment), n_treatment)
        ), 4
    )                                                            AS ci_lower_pp,

    ROUND(
      (cvr_treatment - cvr_control)
      + 1.96 * SQRT(
          SAFE_DIVIDE(cvr_control * (1 - cvr_control), n_control)
          + SAFE_DIVIDE(cvr_treatment * (1 - cvr_treatment), n_treatment)
        ), 4
    )                                                            AS ci_upper_pp
  FROM pivoted
)

SELECT
  day_since_launch,
  n_control,
  n_treatment,
  ROUND(cvr_control   * 100, 3) AS cvr_control_pct,
  ROUND(cvr_treatment * 100, 3) AS cvr_treatment_pct,
  abs_uplift_pp,
  rel_uplift_pct,
  z_statistic,
  ci_lower_pp,
  ci_upper_pp,

  -- Classify each day's result
  CASE
    WHEN ci_lower_pp > 0 THEN 'positive_significant'
    WHEN ci_upper_pp < 0 THEN 'negative_significant'
    ELSE 'inconclusive'
  END                           AS day_result

FROM with_stats
ORDER BY day_since_launch;
