import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatInterface from '../components/ChatInterface';
import './ChatPage.css';

const ChatPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleNewChat = () => {
    window.location.reload();
  };

  return (
    <div className="chat-page">
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Chat History</h2>
          <button 
            className="close-sidebar-btn"
            onClick={toggleSidebar}
          >
            ×
          </button>
        </div>
        <div className="sidebar-content">
          <button className="new-chat-btn" onClick={handleNewChat}>
            + New Chat
          </button>
          <div className="chat-history">
            <div className="chat-history-item">
              Previous conversation 1
            </div>
            <div className="chat-history-item">
              Previous conversation 2
            </div>
          </div>
        </div>
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      <div className="main-content">
        <header className="chat-header">
          <button 
            className="menu-btn"
            onClick={toggleSidebar}
          >
            ☰
          </button>
          <h1>AI Chat Assistant</h1>
        </header>

        <div className="chat-container">
          <ChatInterface />
        </div>
      </div>

      {sidebarOpen && (
        <div 
          className="sidebar-overlay"
          onClick={toggleSidebar}
        />
      )}
    </div>
  );
};

export default ChatPage;