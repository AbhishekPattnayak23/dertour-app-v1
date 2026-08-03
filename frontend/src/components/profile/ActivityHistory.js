import React from 'react';
import { useNavigate } from 'react-router-dom';
import { mockRecentActivity } from '../../utils/mockData';
import '../common/Card.css';
import '../../styles/designTokens.css';

const ActivityHistory = () => {
  const navigate = useNavigate();
  const activities = mockRecentActivity;

  const handleActivityClick = (activity) => {
    if (activity.type === 'chat' && activity.link) {
      navigate('/chat');
    } else if (activity.type === 'document' && activity.link) {
      // Open DocumentViewer modal - for now just navigate to chat
      navigate('/chat');
    } else if (activity.type === 'search') {
      // Navigate back to search results
      navigate('/chat');
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'chat':
        return '';
      case 'document':
        return '';
      case 'search':
        return '';
      default:
        return '';
    }
  };

  return (
    <div className="activity-history card">
      <h3>Recent Activity</h3>
      <div className="activity-list">
        {activities.map((activity, index) => (
          <div
            key={index}
            className="activity-item clickable"
            onClick={() => handleActivityClick(activity)}
          >
            <div className="activity-icon">
              {getActivityIcon(activity.type)}
            </div>
            <div className="activity-details">
              <p className="activity-description">{activity.description}</p>
              <span className="activity-timestamp">{activity.timestamp}</span>
            </div>
            <div className="activity-type-badge">
              {activity.type}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityHistory;
