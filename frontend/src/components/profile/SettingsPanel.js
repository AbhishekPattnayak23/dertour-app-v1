import React, { useState } from 'react';
import { mockUserProfile } from '../../utils/mockData';
import Toggle from '../common/Toggle';
import Select from '../common/Select';
import Toast from '../common/Toast';
import '../common/Card.css';
import '../../styles/designTokens.css';

const SettingsPanel = () => {
  const [settings, setSettings] = useState(mockUserProfile.notificationSettings);
  const [preferences, setPreferences] = useState(mockUserProfile.preferences);
  const [showToast, setShowToast] = useState(false);

  const handleSettingChange = (setting, value) => {
    setSettings({ ...settings, [setting]: value });
    showSavedNotification();
  };

  const handlePreferenceChange = (preference, value) => {
    setPreferences({ ...preferences, [preference]: value });
    showSavedNotification();
  };

  const showSavedNotification = () => {
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const regionOptions = [
    { value: 'europe', label: 'Europe' },
    { value: 'asia-pacific', label: 'Asia-Pacific' },
    { value: 'americas', label: 'Americas' },
    { value: 'africa', label: 'Africa' }
  ];

  const languageOptions = [
    { value: 'en', label: 'English' },
    { value: 'de', label: 'German' },
    { value: 'fr', label: 'French' },
    { value: 'es', label: 'Spanish' }
  ];

  return (
    <div className="settings-panel">
      {/* Account Settings Section */}
      <div className="settings-section card">
        <h3>Account Settings</h3>
        <div className="notification-preferences">
          <h4>Notification Preferences</h4>
          <div className="setting-item">
            <label>Email notifications</label>
            <Toggle
              checked={settings.emailNotifications}
              onChange={(value) => handleSettingChange('emailNotifications', value)}
            />
          </div>
          <div className="setting-item">
            <label>Teams notifications</label>
            <Toggle
              checked={settings.teamsNotifications}
              onChange={(value) => handleSettingChange('teamsNotifications', value)}
            />
          </div>
          <div className="setting-item">
            <label>Urgent alerts</label>
            <Toggle
              checked={settings.urgentAlerts}
              onChange={(value) => handleSettingChange('urgentAlerts', value)}
            />
          </div>
        </div>
      </div>

      {/* Preferences Section */}
      <div className="preferences-section card">
        <h3>Preferences</h3>
        <div className="preference-item">
          <label>Default regions of interest</label>
          <Select
            multiple
            value={preferences.defaultRegions}
            options={regionOptions}
            onChange={(value) => handlePreferenceChange('defaultRegions', value)}
          />
        </div>
        <div className="preference-item">
          <label>Language preferences</label>
          <Select
            value={preferences.language}
            options={languageOptions}
            onChange={(value) => handlePreferenceChange('language', value)}
          />
        </div>
      </div>

      {showToast && (
        <Toast type="success" message="Settings saved" />
      )}
    </div>
  );
};

export default SettingsPanel;
