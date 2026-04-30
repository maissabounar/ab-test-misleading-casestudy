-- =============================================================================
-- 03_guardrail_metrics.sql
-- Guardrail metrics: refund rate, revenue per user, revenue per converter,
-- broken out by experiment group and user_type.
-- Dialect: BigQuery Standard SQL
-- =============================================================================

WITH base AS (
  SELECT
    experiment_group,
    user_type,
    COUNT(DISTINCT user_id)                                      AS n_users,
    SUM(conversion_flag)                                         AS conversions,
    SAFE_DIVIDE(SUM(conversion_flag), COUNT(DISTINCT user_id))   AS cvr,
    SUM(refund_flag)                                             AS refunds,
    SAFE_DIVIDE(SUM(refund_flag), COUNT(DISTINCT user_id))       AS refund_rate_all_users,
    SAFE_DIVIDE(
      SUM(IF(conversion_flag = 1, refund_flag, 0)),
      NULLIF(SUM(conversion_flag), 0)
    )                                                            AS refund_rate_converters,
    AVG(revenue)                                                 AS revenue_per_user,
    SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(conversion_flag), 0))   AS revenue_per_converter,
    SUM(revenue)                                                 AS total_revenue
  FROM `project.dataset.experiment_data`
  GROUP BY 1, 2
),

-- Expected net revenue per user after refund haircut (assume 90% of revenue returned)
with_net AS (
  SELECT
    *,
    revenue_per_user - (refund_rate_all_users * revenue_per_converter * 0.90)
      AS net_revenue_per_user
  FROM base
)

SELECT
  experiment_group,
  user_type,
  n_users,
  conversions,
  ROUND(cvr               * 100, 3)   AS cvr_pct,
  refunds,
  ROUND(refund_rate_all_users  * 100, 3) AS refund_rate_all_pct,
  ROUND(refund_rate_converters * 100, 3) AS refund_rate_conv_pct,
  ROUND(revenue_per_user,      2)        AS revenue_per_user,
  ROUND(revenue_per_converter, 2)        AS revenue_per_converter,
  ROUND(net_revenue_per_user,  2)        AS net_revenue_per_user,
  ROUND(total_revenue,         2)        AS total_revenue
FROM with_net
ORDER BY user_type, experiment_group;
