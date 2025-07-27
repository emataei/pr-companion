import { useState, useEffect } from 'react'

interface NotificationProps {
  readonly id: string
  readonly message: string
  readonly type: 'success' | 'error' | 'warning' | 'info'
  readonly autoClose?: boolean
  readonly duration?: number
  readonly onClose?: (id: string) => void
}

interface NotificationManagerProps {
  readonly maxNotifications?: number
  readonly defaultDuration?: number
}

export interface NotificationData {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  timestamp: Date
  autoClose?: boolean
  duration?: number
}

/**
 * Individual notification component
 * @param id - Unique identifier for the notification
 * @param message - The message to display
 * @param type - Visual type of notification
 * @param autoClose - Whether to auto-close the notification
 * @param duration - How long to show before auto-closing (ms)
 * @param onClose - Callback when notification is closed
 */
function Notification({ 
  id, 
  message, 
  type, 
  autoClose = true, 
  duration = 5000, 
  onClose 
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(true)
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(() => {
        handleClose()
      }, duration)

      return () => clearTimeout(timer)
    }
  }, [autoClose, duration])

  const handleClose = () => {
    setIsAnimating(true)
    setTimeout(() => {
      setIsVisible(false)
      onClose?.(id)
    }, 300) // Animation duration
  }

  if (!isVisible) return null

  const getNotificationStyle = () => {
    const baseStyle = {
      padding: '12px 16px',
      margin: '8px 0',
      borderRadius: '6px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      transition: 'all 0.3s ease',
      transform: isAnimating ? 'translateX(100%)' : 'translateX(0)',
      opacity: isAnimating ? 0 : 1
    }

    const typeStyles = {
      success: { backgroundColor: '#d4edda', color: '#155724', border: '1px solid #c3e6cb' },
      error: { backgroundColor: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb' },
      warning: { backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffeaa7' },
      info: { backgroundColor: '#d1ecf1', color: '#0c5460', border: '1px solid #bee5eb' }
    }

    return { ...baseStyle, ...typeStyles[type] }
  }

  return (
    <div style={getNotificationStyle()}>
      <span>{message}</span>
      <button
        onClick={handleClose}
        style={{
          background: 'none',
          border: 'none',
          fontSize: '18px',
          cursor: 'pointer',
          color: 'inherit',
          opacity: 0.7
        }}
        aria-label="Close notification"
      >
        ×
      </button>
    </div>
  )
}

/**
 * Notification manager component for handling multiple notifications
 * @param maxNotifications - Maximum number of notifications to show
 * @param defaultDuration - Default duration for auto-closing notifications
 */
export function NotificationManager({ 
  maxNotifications = 5, 
  defaultDuration = 5000 
}: NotificationManagerProps) {
  const [notifications, setNotifications] = useState<NotificationData[]>([])

  const addNotification = (notification: Omit<NotificationData, 'id' | 'timestamp'>) => {
    const newNotification: NotificationData = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substring(2, 11),
      timestamp: new Date(),
      duration: notification.duration || defaultDuration
    }

    setNotifications(prev => {
      const updated = [newNotification, ...prev]
      // Keep only the most recent notifications
      return updated.slice(0, maxNotifications)
    })
  }

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id))
  }

  const clearAllNotifications = () => {
    setNotifications([])
  }

  // Expose methods to parent components via a global hook or context
  useEffect(() => {
    // This would typically be handled by a context provider
    // For now, we'll attach to window for demo purposes
    if (typeof window !== 'undefined') {
      (window as any).showNotification = addNotification;
      (window as any).clearNotifications = clearAllNotifications;
    }
  }, [])

  return (
    <section
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 1000,
        minWidth: '300px',
        maxWidth: '400px'
      }}
      aria-label="Notifications"
    >
      {notifications.map(notification => (
        <Notification
          key={notification.id}
          {...notification}
          onClose={removeNotification}
        />
      ))}
    </section>
  )
}

export default NotificationManager
