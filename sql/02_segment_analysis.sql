-- =============================================================================
-- 02_segment_analysis.sql
-- Segment-level conversion uplift: user_type, device_type, browser,
-- country, traffic_source. One row per segment value.
-- Dialect: BigQuery Standard SQL
-- =============================================================================

WITH dimensions AS (
  -- Union all dimensions into a single table for DRY aggregation
  SELECT user_id, experiment_group, conversion_flag,
         'user_type'      AS dimension,
         user_type        AS segment_value
  FROM `project.dataset.experiment_data`

  UNION ALL
  SELECT user_id, experiment_group, conversion_flag,
         'device_type', device_type
  FROM `project.dataset.experiment_data`

  UNION ALL
  SELECT user_id, experiment_group, conversion_flag,
         'browser', browser
  FROM `project.dataset.experiment_data`

  UNION ALL
  SELECT user_id, experiment_group, conversion_flag,
         'country', country
  FROM `project.dataset.experiment_data`

  UNION ALL
  SELECT user_id, experiment_group, conversion_flag,
         'traffic_source', traffic_source
  FROM `project.dataset.experiment_data`
),

aggregated AS (
  SELECT
    dimension,
    segment_value,
    experiment_group,
    COUNT(DISTINCT user_id)                                      AS n_users,
    SUM(conversion_flag)                                         AS conversions,
    SAFE_DIVIDE(SUM(conversion_flag), COUNT(DISTINCT user_id))   AS cvr
  FROM dimensions
  GROUP BY 1, 2, 3
),

pivoted AS (
  SELECT
    dimension,
    segment_value,
    MAX(IF(experiment_group = 'control',   n_users,     NULL)) AS n_control,
    MAX(IF(experiment_group = 'treatment', n_users,     NULL)) AS n_treatment,
    MAX(IF(experiment_group = 'control',   conversions, NULL)) AS conv_control,
    MAX(IF(experiment_group = 'treatment', conversions, NULL)) AS conv_treatment,
    MAX(IF(experiment_group = 'control',   cvr,         NULL)) AS cvr_control,
    MAX(IF(experiment_group = 'treatment', cvr,         NULL)) AS cvr_treatment
  FROM aggregated
  GROUP BY 1, 2
)

SELECT
  dimension,
  segment_value,
  n_control,
  n_treatment,
  ROUND(cvr_control   * 100, 3)                                 AS cvr_control_pct,
  ROUND(cvr_treatment * 100, 3)                                 AS cvr_treatment_pct,
  ROUND((cvr_treatment - cvr_control) * 100, 4)                 AS abs_uplift_pp,
  ROUND(
    SAFE_DIVIDE(cvr_treatment - cvr_control, cvr_control) * 100, 2
  )                                                             AS rel_uplift_pct,

  -- z-statistic for each segment
  ROUND(
    SAFE_DIVIDE(
      cvr_treatment - cvr_control,
      SQRT(
        SAFE_DIVIDE(cvr_control * (1 - cvr_control), n_control)
        + SAFE_DIVIDE(cvr_treatment * (1 - cvr_treatment), n_treatment)
      )
    ), 4
  )                                                             AS z_statistic,

  -- Flag segments with fewer than 500 users per arm as underpowered
  CASE
    WHEN n_control < 500 OR n_treatment < 500 THEN 'underpowered'
    WHEN ABS(
      SAFE_DIVIDE(
        cvr_treatment - cvr_control,
        SQRT(
          SAFE_DIVIDE(cvr_control * (1 - cvr_control), n_control)
          + SAFE_DIVIDE(cvr_treatment * (1 - cvr_treatment), n_treatment)
        )
      )
    ) >= 1.96 THEN 'significant (uncorrected)'
    ELSE 'not significant'
  END                                                           AS significance_flag

FROM pivoted
WHERE n_control  >= 100
  AND n_treatment >= 100
ORDER BY dimension, rel_uplift_pct DESC;
