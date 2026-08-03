import React, { useState, useEffect } from 'react';
import './ConversationHistory.css';

const ConversationHistory = ({ 
  conversations = [], 
  activeConversationId, 
  onConversationSelect, 
  onNewConversation,
  onDeleteConversation 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredConversations, setFilteredConversations] = useState([]);

  useEffect(() => {
    const filtered = conversations.filter(conversation =>
      conversation.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conversation.preview.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredConversations(filtered);
  }, [conversations, searchTerm]);

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 60) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else if (days < 7) {
      return `${days}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const truncateText = (text, maxLength = 50) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  const handleDeleteClick = (e, conversationId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      onDeleteConversation(conversationId);
    }
  };

  return (
    <div className="conversation-history">
      <div className="conversation-history-header">
        <button 
          className="new-conversation-btn"
          onClick={onNewConversation}
          title="Start new conversation"
        >
          <span className="icon">+</span>
          New Conversation
        </button>
      </div>

      <div className="search-container">
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="conversations-list">
        {filteredConversations.length === 0 ? (
          <div className="empty-state">
            {searchTerm ? 'No conversations found' : 'No conversations yet'}
          </div>
        ) : (
          filteredConversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conversation-item ${
                activeConversationId === conversation.id ? 'active' : ''
              }`}
              onClick={() => onConversationSelect(conversation.id)}
            >
              <div className="conversation-content">
                <div className="conversation-title">
                  {truncateText(conversation.title)}
                </div>
                <div className="conversation-preview">
                  {truncateText(conversation.preview)}
                </div>
                <div className="conversation-meta">
                  <span className="conversation-date">
                    {formatDate(conversation.updatedAt)}
                  </span>
                  <span className="message-count">
                    {conversation.messageCount} messages
                  </span>
                </div>
              </div>
              <button
                className="delete-conversation-btn"
                onClick={(e) => handleDeleteClick(e, conversation.id)}
                title="Delete conversation"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export { ConversationHistory };