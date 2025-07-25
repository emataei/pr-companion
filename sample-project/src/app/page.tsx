'use client'
import { useState } from 'react'
import { UserProfile } from '../components/UserProfile'
import { UserSettings } from '../components/UserSettings'
import { UserActivityLog } from '../components/UserActivityLog'
import { AnalyticsDashboard } from '../components/AnalyticsDashboard'

interface HealthStatus {
  status: 'ok' | 'error';
  timestamp: string;
  version: string;
  uptime: number;
  environment: string;
}

interface UserCardProps {
  readonly userId?: string
  readonly title: string
  readonly variant?: 'primary' | 'secondary'
}

function UserCard({ userId, title, variant = 'primary' }: UserCardProps) {
  const [isLoading, setIsLoading] = useState(false)
  
  // Use environment variable for API configuration
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || '/api'
  
  const handleSaveUser = async (formData: FormData) => {
    setIsLoading(true)
    try {
      // Process form data
      const userData = {
        name: formData.get('name') as string,
        email: formData.get('email') as string,
      }
      
      if (userId) {
        await fetch(`${apiUrl}/users/${userId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData)
        })
      }
      
      console.log('User saved successfully')
    } catch (error) {
      console.error('Failed to save user:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="user-card">
      <UserProfile
        title={title}
        onSave={handleSaveUser}
        variant={variant}
        userId={userId}
      />
      {isLoading && <span>Loading...</span>}
    </div>
  )
}

// Proper Next.js page component  
export default function HomePage() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(false);

  const checkHealth = async () => {
    setIsLoadingHealth(true);
    try {
      const response = await fetch('/api/health');
      const data: HealthStatus = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Failed to fetch health status:', error);
      setHealthStatus({
        status: 'error',
        timestamp: new Date().toISOString(),
        version: 'unknown',
        uptime: 0,
        environment: 'unknown'
      });
    } finally {
      setIsLoadingHealth(false);
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <main style={{padding: '2rem', minHeight: '100vh', backgroundColor: '#f0f0f0'}}>
      <h1 style={{color: '#333', marginBottom: '2rem'}}>System Dashboard</h1>
      
      <div style={{marginBottom: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: 'white'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
          <h3>System Health Status</h3>
          <button 
            onClick={checkHealth}
            disabled={isLoadingHealth}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoadingHealth ? 'not-allowed' : 'pointer',
              opacity: isLoadingHealth ? 0.6 : 1
            }}
          >
            {isLoadingHealth ? 'Checking...' : 'Check Health'}
          </button>
        </div>
        
        {healthStatus && (
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
            <div>
              <strong>Status:</strong> 
              <span style={{
                color: healthStatus.status === 'ok' ? 'green' : 'red',
                marginLeft: '0.5rem'
              }}>
                {healthStatus.status.toUpperCase()}
              </span>
            </div>
            <div><strong>Version:</strong> {healthStatus.version}</div>
            <div><strong>Environment:</strong> {healthStatus.environment}</div>
            <div><strong>Uptime:</strong> {formatUptime(healthStatus.uptime)}</div>
            <div style={{gridColumn: '1 / -1'}}>
              <strong>Last Check:</strong> {new Date(healthStatus.timestamp).toLocaleString()}
            </div>
          </div>
        )}
      </div>

      <p style={{color: '#666', marginBottom: '1rem'}}>
        Sample application with health monitoring and user profile features.
      </p>
      
      <UserCard 
        userId="1"
        title="Edit User Profile"
        variant="primary"
      />
      
      <div style={{marginTop: '2rem'}}>
        <UserCard 
          title="Create New User"
          variant="secondary"
        />
      </div>
      
      <div style={{marginTop: '2rem'}}>
        <h2>User Settings</h2>
        <UserSettings 
          userId="demo-user-123"
          onSettingsChange={(settings) => {
            console.log('Settings updated:', settings);
          }}
        />
      </div>

      <div style={{marginTop: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px'}}>
        <h2>User Activity Log</h2>
        <UserActivityLog userId="demo-user-123" />
      </div>

      <div style={{marginTop: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px'}}>
        <h2>Analytics Dashboard</h2>
        <AnalyticsDashboard userId="550e8400-e29b-41d4-a716-446655440000" />
      </div>
      
      <div style={{marginTop: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px'}}>
        <h3>New Features Implemented:</h3>
        <ul>
          <li>User data loading from API</li>
          <li>Enhanced form handling</li>
          <li>Improved accessibility</li>
          <li>Better error handling</li>
          <li>Updated styling with animations</li>
          <li>User settings management system</li>
          <li>Real-time settings synchronization</li>
          <li>User activity tracking and logging</li>
          <li>Activity filtering and pagination</li>
          <li>Comprehensive analytics dashboard with metrics tracking</li>
          <li>Analytics API with validation and mock data</li>
        </ul>
      </div>
    </main>
  )
}
