import React, { useState, useEffect } from 'react';

interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  privacy: {
    publicProfile: boolean;
    shareAnalytics: boolean;
  };
  language: string;
}

interface UserSettingsProps {
  readonly userId: string;
  readonly onSettingsChange?: (settings: UserSettings) => void;
}

export function UserSettings({ userId, onSettingsChange }: UserSettingsProps) {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load user settings on component mount
  useEffect(() => {
    loadSettings();
  }, [userId]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/users/${userId}/settings`);
      const result = await response.json();
      
      if (result.success) {
        setSettings(result.data);
      } else {
        setError(result.error || 'Failed to load settings');
      }
    } catch (err) {
      setError('Network error loading settings');
      console.error('Settings load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async (newSettings: UserSettings) => {
    try {
      setSaving(true);
      setError(null);
      
      const response = await fetch(`/api/users/${userId}/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSettings),
      });
      
      const result = await response.json();
      
      if (result.success) {
        setSettings(result.data);
        onSettingsChange?.(result.data);
      } else {
        setError(result.error || 'Failed to save settings');
      }
    } catch (err) {
      setError('Network error saving settings');
      console.error('Settings save error:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleThemeChange = (theme: UserSettings['theme']) => {
    if (!settings) return;
    const updatedSettings = { ...settings, theme };
    saveSettings(updatedSettings);
  };

  const handleNotificationChange = (key: keyof UserSettings['notifications'], value: boolean) => {
    if (!settings) return;
    const updatedSettings = {
      ...settings,
      notifications: { ...settings.notifications, [key]: value }
    };
    saveSettings(updatedSettings);
  };

  const handlePrivacyChange = (key: keyof UserSettings['privacy'], value: boolean) => {
    if (!settings) return;
    const updatedSettings = {
      ...settings,
      privacy: { ...settings.privacy, [key]: value }
    };
    saveSettings(updatedSettings);
  };

  const handleLanguageChange = (language: string) => {
    if (!settings) return;
    const updatedSettings = { ...settings, language };
    saveSettings(updatedSettings);
  };

  if (loading) {
    return (
      <div className="settings-container" data-testid="settings-loading">
        <div className="loading-spinner">Loading settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="settings-container" data-testid="settings-error">
        <div className="settings-error-message">
          Error: {error}
          <button onClick={loadSettings} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!settings) {
    return null;
  }

  return (
    <div className="settings-container" data-testid="user-settings">
      <h2>User Settings</h2>
      
      {saving && <div className="saving-indicator">Saving...</div>}
      
      {/* Theme Settings */}
      <section className="settings-section">
        <h3>Appearance</h3>
        <div className="setting-group">
          <label htmlFor="theme-select">Theme:</label>
          <select
            id="theme-select"
            value={settings.theme}
            onChange={(e) => handleThemeChange(e.target.value as UserSettings['theme'])}
            disabled={saving}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="auto">Auto</option>
          </select>
        </div>
      </section>

      {/* Notification Settings */}
      <section className="settings-section">
        <h3>Notifications</h3>
        <div className="setting-group">
          <label>
            <input
              type="checkbox"
              checked={settings.notifications.email}
              onChange={(e) => handleNotificationChange('email', e.target.checked)}
              disabled={saving}
            />
            Email notifications
          </label>
        </div>
        <div className="setting-group">
          <label>
            <input
              type="checkbox"
              checked={settings.notifications.push}
              onChange={(e) => handleNotificationChange('push', e.target.checked)}
              disabled={saving}
            />
            Push notifications
          </label>
        </div>
        <div className="setting-group">
          <label>
            <input
              type="checkbox"
              checked={settings.notifications.sms}
              onChange={(e) => handleNotificationChange('sms', e.target.checked)}
              disabled={saving}
            />
            SMS notifications
          </label>
        </div>
      </section>

      {/* Privacy Settings */}
      <section className="settings-section">
        <h3>Privacy</h3>
        <div className="setting-group">
          <label>
            <input
              type="checkbox"
              checked={settings.privacy.publicProfile}
              onChange={(e) => handlePrivacyChange('publicProfile', e.target.checked)}
              disabled={saving}
            />
            Public profile
          </label>
        </div>
        <div className="setting-group">
          <label>
            <input
              type="checkbox"
              checked={settings.privacy.shareAnalytics}
              onChange={(e) => handlePrivacyChange('shareAnalytics', e.target.checked)}
              disabled={saving}
            />
            Share analytics
          </label>
        </div>
      </section>

      {/* Language Settings */}
      <section className="settings-section">
        <h3>Language</h3>
        <div className="setting-group">
          <label htmlFor="language-select">Language:</label>
          <select
            id="language-select"
            value={settings.language}
            onChange={(e) => handleLanguageChange(e.target.value)}
            disabled={saving}
          >
            <option value="en-US">English (US)</option>
            <option value="en-GB">English (UK)</option>
            <option value="es-ES">Español</option>
            <option value="fr-FR">Français</option>
            <option value="de-DE">Deutsch</option>
          </select>
        </div>
      </section>
    </div>
  );
}
