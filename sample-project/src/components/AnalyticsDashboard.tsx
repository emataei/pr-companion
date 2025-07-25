import React, { useState, useEffect } from 'react'
import styles from './AnalyticsDashboard.module.css'

interface AnalyticsData {
  userId?: string
  metric: string
  value: number
  date: string
}

interface AnalyticsSummary {
  totalPageviews: number
  totalSessions: number
  avgEngagement: number
  uniqueUsers: number
}

interface AnalyticsResponse {
  success: boolean
  data: AnalyticsData[]
  summary: AnalyticsSummary
  query: {
    userId?: string
    startDate?: string
    endDate?: string
    metric: string
  }
}

interface AnalyticsDashboardProps {
  userId?: string
  className?: string
}

export function AnalyticsDashboard({ userId, className }: AnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMetric, setSelectedMetric] = useState<string>('all')

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        metric: selectedMetric,
        ...(userId && { userId }),
      })

      const response = await fetch(`/api/analytics?${params}`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch analytics')
      }

      setAnalytics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [userId, selectedMetric])

  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'pageviews':
        return '📄'
      case 'sessions':
        return '⏱️'
      case 'engagement':
        return '💡'
      default:
        return '📊'
    }
  }

  const formatValue = (metric: string, value: number) => {
    if (metric === 'engagement') {
      return `${value}%`
    }
    return value.toLocaleString()
  }

  if (loading) {
    return (
      <div className={`${styles.analyticsDashboard} ${className || ''}`}>
        <div className={styles.loadingSpinner}>
          <div className={styles.spinner}></div>
          <p>Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`${styles.analyticsDashboard} error ${className || ''}`}>
        <div className={styles.errorMessage}>
          <h3>Error Loading Analytics</h3>
          <p>{error}</p>
          <button onClick={fetchAnalytics} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!analytics) {
    return null
  }

  return (
    <div className={`${styles.analyticsDashboard} ${className || ''}`}>
      <div className={styles.dashboardHeader}>
        <h2>Analytics Dashboard</h2>
        <div className={styles.metricSelector}>
          <label htmlFor="metric-select">Filter by metric:</label>
          <select
            id="metric-select"
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
          >
            <option value="all">All Metrics</option>
            <option value="pageviews">Page Views</option>
            <option value="sessions">Sessions</option>
            <option value="engagement">Engagement</option>
          </select>
        </div>
      </div>

      <div className={styles.summaryCards}>
        <div className={styles.summaryCard}>
          <div className={styles.cardIcon}>📄</div>
          <div className={styles.cardContent}>
            <h3>Total Page Views</h3>
            <p className={styles.metricValue}>{analytics.summary.totalPageviews}</p>
          </div>
        </div>

        <div className={styles.summaryCard}>
          <div className={styles.cardIcon}>⏱️</div>
          <div className={styles.cardContent}>
            <h3>Total Sessions</h3>
            <p className={styles.metricValue}>{analytics.summary.totalSessions}</p>
          </div>
        </div>

        <div className={styles.summaryCard}>
          <div className={styles.cardIcon}>💡</div>
          <div className={styles.cardContent}>
            <h3>Avg Engagement</h3>
            <p className={styles.metricValue}>{analytics.summary.avgEngagement}%</p>
          </div>
        </div>

        <div className={styles.summaryCard}>
          <div className={styles.cardIcon}>👥</div>
          <div className={styles.cardContent}>
            <h3>Unique Users</h3>
            <p className={styles.metricValue}>{analytics.summary.uniqueUsers}</p>
          </div>
        </div>
      </div>

      <div className={styles.detailedData}>
        <h3>Detailed Metrics</h3>
        {analytics.data.length === 0 ? (
          <p className={styles.noData}>No analytics data available for the selected filters.</p>
        ) : (
          <div className={styles.dataTable}>
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Value</th>
                  <th>Date</th>
                  {!userId && <th>User ID</th>}
                </tr>
              </thead>
              <tbody>
                {analytics.data.map((item) => (
                  <tr key={`${item.userId}-${item.metric}-${item.date}`}>
                    <td>
                      <span className={styles.metricLabel}>
                        {getMetricIcon(item.metric)} {item.metric}
                      </span>
                    </td>
                    <td className={styles.metricValue}>
                      {formatValue(item.metric, item.value)}
                    </td>
                    <td className={styles.dateValue}>
                      {new Date(item.date).toLocaleDateString()}
                    </td>
                    {!userId && (
                      <td className={styles.userId}>
                        {item.userId ? item.userId.slice(-8) : 'N/A'}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
