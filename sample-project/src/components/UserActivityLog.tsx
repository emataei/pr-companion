'use client';

import { useState, useEffect } from 'react';

interface UserActivity {
  type: 'login' | 'logout' | 'profile_update' | 'settings_change' | 'api_call';
  timestamp: string;
  metadata?: {
    userAgent?: string;
    ipAddress?: string;
    duration?: number;
  };
}

interface ActivityResponse {
  success: boolean;
  data?: {
    activities: UserActivity[];
    total: number;
    limit: number;
    offset: number;
  };
  error?: string;
}

interface UserActivityLogProps {
  readonly userId: string;
}

export function UserActivityLog({ userId }: UserActivityLogProps) {
  const [activities, setActivities] = useState<UserActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  const activityTypes = [
    { value: 'all', label: 'All Activities' },
    { value: 'login', label: 'Login' },
    { value: 'logout', label: 'Logout' },
    { value: 'profile_update', label: 'Profile Update' },
    { value: 'settings_change', label: 'Settings Change' },
    { value: 'api_call', label: 'API Call' },
  ];

  const fetchActivities = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      if (filterType !== 'all') {
        queryParams.set('type', filterType);
      }
      queryParams.set('limit', '20');

      const response = await fetch(`/api/users/${userId}/activities?${queryParams}`);
      const data: ActivityResponse = await response.json();

      if (data.success && data.data) {
        setActivities(data.data.activities);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch activities');
      }
    } catch (err) {
      setError('Network error occurred');
      console.error('Error fetching activities:', err);
    } finally {
      setLoading(false);
    }
  };

  const logActivity = async (type: UserActivity['type']) => {
    try {
      const activity: UserActivity = {
        type,
        timestamp: new Date().toISOString(),
        metadata: {
          userAgent: navigator.userAgent,
          duration: type === 'api_call' ? Math.floor(Math.random() * 1000) : undefined,
        },
      };

      const response = await fetch(`/api/users/${userId}/activities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(activity),
      });

      const data = await response.json();
      if (data.success) {
        // Refresh activities after logging
        fetchActivities();
      } else {
        setError('Failed to log activity');
      }
    } catch (err) {
      setError('Failed to log activity');
      console.error('Error logging activity:', err);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, [userId, filterType]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'login': return '🔑';
      case 'logout': return '🚪';
      case 'profile_update': return '👤';
      case 'settings_change': return '⚙️';
      case 'api_call': return '🔌';
      default: return '📝';
    }
  };

  if (loading) {
    return (
      <div className="activity-log">
        <h3>User Activity Log</h3>
        <div className="loading">Loading activities...</div>
      </div>
    );
  }

  return (
    <div className="activity-log">
      <div className="activity-header">
        <h3>User Activity Log</h3>
        
        <div className="activity-controls">
          <select 
            value={filterType} 
            onChange={(e) => setFilterType(e.target.value)}
            className="filter-select"
          >
            {activityTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          
          <button 
            onClick={() => fetchActivities()}
            className="refresh-btn"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="quick-actions">
        <h4>Quick Actions:</h4>
        <div className="action-buttons">
          <button onClick={() => logActivity('login')}>Log Login</button>
          <button onClick={() => logActivity('logout')}>Log Logout</button>
          <button onClick={() => logActivity('profile_update')}>Log Profile Update</button>
          <button onClick={() => logActivity('settings_change')}>Log Settings Change</button>
          <button onClick={() => logActivity('api_call')}>Log API Call</button>
        </div>
      </div>

      {error && <div className="error">Error: {error}</div>}

      <div className="activities-list">
        {activities.length === 0 ? (
          <div className="no-activities">
            No activities found. Use the quick actions above to generate some test data.
          </div>
        ) : (
          activities.map((activity) => (
            <div key={`${activity.type}-${activity.timestamp}`} className="activity-item">
              <div className="activity-icon">
                {getActivityIcon(activity.type)}
              </div>
              <div className="activity-content">
                <div className="activity-type">
                  {activity.type.replace('_', ' ').toUpperCase()}
                </div>
                <div className="activity-timestamp">
                  {formatTimestamp(activity.timestamp)}
                </div>
                {activity.metadata?.duration && (
                  <div className="activity-duration">
                    Duration: {activity.metadata.duration}ms
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
