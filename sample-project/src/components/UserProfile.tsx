// This component follows the Copilot instructions correctly
// Updated to test PR visual generation workflow
import { useState, useEffect } from 'react'

interface UserProfileProps {
  readonly title: string
  readonly onSave: (data: FormData) => void
  readonly variant?: 'primary' | 'secondary'
  readonly userId?: string
  readonly isEditable?: boolean
}

interface UserData {
  name: string
  email: string
  bio?: string
  avatar?: string
  phone?: string
  location?: string
  lastLogin?: Date
  preferences?: UserPreferences
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  notifications: boolean
  language: string
}

/**
 * UserProfile component for displaying and editing user information
 * @param title - The title to display
 * @param onSave - Callback function when saving user data
 * @param variant - Visual style variant
 * @param userId - Optional user ID for loading existing data
 * @returns JSX element for user profile
 */
export function UserProfile({ title, onSave, variant = 'primary', userId }: UserProfileProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [userData, setUserData] = useState<UserData | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Load user data when userId is provided
  useEffect(() => {
    if (userId) {
      const loadUserData = async () => {
        try {
          // Simulate API call
          const response = await fetch(`/api/users/${userId}`)
          const data = await response.json()
          setUserData(data)
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to load user data'
          setError(errorMessage)
        }
      }
      loadUserData()
    }
  }, [userId])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const formData = new FormData(event.currentTarget)
      await Promise.resolve(onSave(formData))
      setSuccessMessage('Profile updated successfully!')
      setIsEditing(false)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleEditMode = () => {
    setIsEditing(!isEditing)
    setError(null)
    setSuccessMessage(null)
  }

  return (
    <main className={`user-profile user-profile--${variant}`}>
      <div className="profile-header">
        <h2>{title}</h2>
        {userData && !isEditing && (
          <button 
            type="button" 
            onClick={toggleEditMode}
            className="edit-button"
            aria-label="Edit profile"
          >
            Edit Profile
          </button>
        )}
      </div>

      {successMessage && (
        <div className="success-message" role="alert" aria-live="polite">
          ✓ {successMessage}
        </div>
      )}

      {userData && !isEditing ? (
        // Display mode
        <div className="profile-display">
          {userData.avatar && (
            <div className="avatar-container">
              <img 
                src={userData.avatar} 
                alt={`${userData.name}'s avatar`}
                className="user-avatar"
              />
            </div>
          )}
          <div className="profile-info">
            <div className="info-item">
              <label>Name:</label>
              <span>{userData.name}</span>
            </div>
            <div className="info-item">
              <label>Email:</label>
              <span>{userData.email}</span>
            </div>
            {userData.phone && (
              <div className="info-item">
                <label>Phone:</label>
                <span>{userData.phone}</span>
              </div>
            )}
            {userData.location && (
              <div className="info-item">
                <label>Location:</label>
                <span>{userData.location}</span>
              </div>
            )}
            {userData.bio && (
              <div className="info-item">
                <label>Bio:</label>
                <p>{userData.bio}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        // Edit mode
        <form onSubmit={handleSubmit} aria-label="User profile form">
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input 
              id="name"
              name="name"
              type="text"
              required
              defaultValue={userData?.name || ''}
              aria-describedby="name-help"
            />
            <div id="name-help" className="help-text">
              Enter your full name
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input 
              id="email"
              name="email"
              type="email"
              required
              defaultValue={userData?.email || ''}
              aria-describedby="email-help"
            />
            <div id="email-help" className="help-text">
              Enter a valid email address
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone (Optional)</label>
            <input 
              id="phone"
              name="phone"
              type="tel"
              defaultValue={userData?.phone || ''}
              aria-describedby="phone-help"
            />
            <div id="phone-help" className="help-text">
              Enter your phone number
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="location">Location (Optional)</label>
            <input 
              id="location"
              name="location"
              type="text"
              defaultValue={userData?.location || ''}
              aria-describedby="location-help"
            />
            <div id="location-help" className="help-text">
              Enter your city and country
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="bio">Bio (Optional)</label>
            <textarea 
              id="bio"
              name="bio"
              rows={4}
              defaultValue={userData?.bio || ''}
              aria-describedby="bio-help"
            />
            <div id="bio-help" className="help-text">
              Tell us about yourself
            </div>
          </div>

          {error && (
            <div className="error-message" role="alert" aria-live="polite">
              ✗ {error}
            </div>
          )}

          <div className="form-actions">
            <button 
              type="submit" 
              disabled={isLoading}
              className="save-button"
              aria-label={isLoading ? 'Saving...' : 'Save profile'}
            >
              {isLoading ? 'Saving...' : 'Save Profile'}
            </button>
            {userData && (
              <button 
                type="button" 
                onClick={toggleEditMode}
                className="cancel-button"
                disabled={isLoading}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      )}
    </main>
  )
}
