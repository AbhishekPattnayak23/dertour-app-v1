import { useChat } from "../../hooks/useChat";
import ConversationHistory from "./ConversationHistory";
import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';

const MessageBubble = ({ message, isOwnMessage }) => {
  return (
    <div className={`message-bubble ${isOwnMessage ? 'own-message' : 'other-message'}`}>
      <div className="message-header">
        <span className="sender-name">{message.sender}</span>
        <span className="message-time">{message.timestamp}</span>
      </div>
      <div className="message-content">{message.content}</div>
    </div>
  );
};

const MessageList = ({ messages, currentUser }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <MessageBubble
          key={index}
          message={message}
          isOwnMessage={message.sender === currentUser}
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

const MessageInput = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <div className="input-container">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={disabled}
          className="message-textarea"
          rows="1"
        />
        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className="send-button"
        >
          Send
        </button>
      </div>
    </form>
  );
};

const ConversationItem = ({ conversation, isActive, onClick }) => {
  return (
    <div
      className={`conversation-item ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      <div className="conversation-avatar">
        {conversation.name.charAt(0).toUpperCase()}
      </div>
      <div className="conversation-details">
        <div className="conversation-name">{conversation.name}</div>
        <div className="conversation-preview">{conversation.lastMessage}</div>
      </div>
      <div className="conversation-meta">
        <div className="conversation-time">{conversation.lastMessageTime}</div>
        {conversation.unreadCount > 0 && (
          <div className="unread-badge">{conversation.unreadCount}</div>
        )}
      </div>
    </div>
  );
};

const ConversationList = ({ conversations, activeConversationId, onConversationSelect }) => {
  return (
    <div className="conversation-list">
      <div className="conversation-list-header">
        <h3>Conversations</h3>
      </div>
      <div className="conversation-list-content">
        {conversations.map((conversation) => (
          <ConversationItem
            key={conversation.id}
            conversation={conversation}
            isActive={conversation.id === activeConversationId}
            onClick={() => onConversationSelect(conversation.id)}
          />
        ))}
      </div>
    </div>
  );
};

const ChatHeader = ({ activeConversation }) => {
  if (!activeConversation) {
    return (
      <div className="chat-header">
        <div className="chat-title">Select a conversation</div>
      </div>
    );
  }

  return (
    <div className="chat-header">
      <div className="chat-avatar">
        {activeConversation.name.charAt(0).toUpperCase()}
      </div>
      <div className="chat-info">
        <div className="chat-title">{activeConversation.name}</div>
        <div className="chat-status">Online</div>
      </div>
    </div>
  );
};

export const ChatInterface = ({
  conversations = [],
  messages = [],
  currentUser = 'You',
  activeConversationId = null,
  onConversationSelect = () => {},
  onSendMessage = () => {},
  loading = false
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const activeConversation = conversations.find(
    (conv) => conv.id === activeConversationId
  );

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="chat-interface">
      <div className={`chat-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <ConversationList
          conversations={conversations}
          activeConversationId={activeConversationId}
          onConversationSelect={onConversationSelect}
        />
      </div>
      
      <div className="chat-main">
        <div className="chat-main-header">
          <button
            className="sidebar-toggle"
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
          <ChatHeader activeConversation={activeConversation} />
        </div>
        
        <div className="chat-content">
          {activeConversationId ? (
            <>
              <MessageList messages={messages} currentUser={currentUser} />
              <MessageInput
                onSendMessage={onSendMessage}
                disabled={loading}
              />
            </>
          ) : (
            <div className="no-conversation-selected">
              <div className="no-conversation-message">
                <h3>Welcome to Chat</h3>
                <p>Select a conversation from the sidebar to start chatting</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};