import React from 'react';
import { mockUserProfile } from '../../utils/mockData';
import Avatar from '../common/Avatar';
import '../common/Card.css';
import '../../styles/designTokens.css';

const ProfileCard = () => {
  const profile = mockUserProfile;

  return (
    <div className="profile-card card">
      <div className="profile-info">
        <div className="profile-avatar">
          <Avatar
            src={profile.profilePicture}
            alt={profile.name}
            size="large"
          />
        </div>
        <div className="profile-details">
          <h2 className="profile-name">{profile.name}</h2>
          <p className="profile-email">{profile.email}</p>
          <p className="profile-department">{profile.department}</p>
          <p className="profile-role">{profile.role}</p>
        </div>
      </div>
    </div>
  );
};

export default ProfileCard;
