import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

const MessageList = ({ messages = [], isLoading = false }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const renderSources = (sources) => {
    if (!sources || sources.length === 0) return null;

    return (
    {messages.length === 0 && (
      <div className="welcome-message">
        <p>Hello Sarah! I'm your Dertour Travel Knowledge Assistant. Ask me about travel risks, safety guidelines, or destination information.</p>
      </div>
    )}
      <div className="message-sources">
        <div className="sources-label">Sources:</div>
        <div className="sources-list">
          {sources.map((source, index) => (
            <div key={index} className="source-item">
              <span className="source-number">[{index + 1}]</span>
              <span className="source-title">{source.title || source.name}</span>
              {source.url && (
                <a 
                  href={source.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="source-link"
                >
                  View
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderMessage = (message, index) => {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';

    return (
    {messages.length === 0 && (
      <div className="welcome-message">
        <p>Hello Sarah! I'm your Dertour Travel Knowledge Assistant. Ask me about travel risks, safety guidelines, or destination information.</p>
      </div>
    )}
      <div 
        key={message.id || index} 
        className={`message ${isUser ? 'message-user' : 'message-assistant'}`}
      >
        <div className="message-avatar">
          {isUser ? (
            <div className="avatar-user">U</div>
          ) : (
            <div className="avatar-assistant">AI</div>
          )}
        </div>
        <div className="message-content">
          <div className="message-bubble">
            <div className="message-text">
              {message.content}
            </div>
            {message.timestamp && (
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            )}
          </div>
          {isAssistant && renderSources(message.sources)}
        </div>
      </div>
    );
  };

  const renderEmptyState = () => (
    <div className="empty-state">
      <div className="empty-state-icon">💬</div>
      <h3>Start a conversation</h3>
      <p>Ask me anything and I'll help you find the information you need.</p>
    </div>
  );

  const renderLoadingMessage = () => (
    <div className="message message-assistant">
      <div className="message-avatar">
        <div className="avatar-assistant">AI</div>
      </div>
      <div className="message-content">
        <div className="message-bubble">
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    {messages.length === 0 && (
      <div className="welcome-message">
        <p>Hello Sarah! I'm your Dertour Travel Knowledge Assistant. Ask me about travel risks, safety guidelines, or destination information.</p>
      </div>
    )}
    <div className="message-list">
      <div className="messages-container">
        {messages.length === 0 && !isLoading ? (
          renderEmptyState()
        ) : (
          <>
            {messages.map(renderMessage)}
            {isLoading && renderLoadingMessage()}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
      <style jsx>{`
        .message-list {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          background: #f8f9fa;
        }

        .messages-container {
          max-width: 800px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .message {
          display: flex;
          gap: 0.75rem;
          max-width: 100%;
        }

        .message-user {
          flex-direction: row-reverse;
        }

        .message-user .message-content {
          align-items: flex-end;
        }

        .message-assistant .message-content {
          align-items: flex-start;
        }

        .message-avatar {
          flex-shrink: 0;
        }

        .avatar-user,
        .avatar-assistant {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 0.875rem;
        }

        .avatar-user {
          background: #007bff;
          color: white;
        }

        .avatar-assistant {
          background: #6c757d;
          color: white;
        }

        .message-content {
          display: flex;
          flex-direction: column;
          max-width: 70%;
          gap: 0.5rem;
        }

        .message-bubble {
          padding: 0.75rem 1rem;
          border-radius: 1rem;
          position: relative;
        }

        .message-user .message-bubble {
          background: #007bff;
          color: white;
          border-bottom-right-radius: 0.25rem;
        }

        .message-assistant .message-bubble {
          background: white;
          color: #333;
          border: 1px solid #e9ecef;
          border-bottom-left-radius: 0.25rem;
        }

        .message-text {
          line-height: 1.5;
          word-wrap: break-word;
        }

        .message-timestamp {
          font-size: 0.75rem;
          opacity: 0.7;
          margin-top: 0.25rem;
        }

        .message-sources {
          margin-top: 0.5rem;
          padding: 0.75rem;
          background: #f8f9fa;
          border-radius: 0.5rem;
          border: 1px solid #e9ecef;
        }

        .sources-label {
          font-size: 0.875rem;
          font-weight: 600;
          color: #6c757d;
          margin-bottom: 0.5rem;
        }

        .sources-list {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .source-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
        }

        .source-number {
          color: #007bff;
          font-weight: 600;
          min-width: 1.5rem;
        }

        .source-title {
          flex: 1;
          color: #333;
        }

        .source-link {
          color: #007bff;
          text-decoration: none;
          font-size: 0.75rem;
        }

        .source-link:hover {
          text-decoration: underline;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 3rem 1rem;
          text-align: center;
          color: #6c757d;
        }

        .empty-state-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .empty-state h3 {
          margin: 0 0 0.5rem 0;
          color: #333;
        }

        .empty-state p {
          margin: 0;
          max-width: 300px;
        }

        .typing-indicator {
          display: flex;
          gap: 0.25rem;
        }

        .typing-indicator span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #6c757d;
          animation: typing 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(1) {
          animation-delay: -0.32s;
        }

        .typing-indicator span:nth-child(2) {
          animation-delay: -0.16s;
        }

        @keyframes typing {
          0%, 80%, 100% {
            opacity: 0.3;
            transform: scale(0.8);
          }
          40% {
            opacity: 1;
            transform: scale(1);
          }
        }

        @media (max-width: 768px) {
          .message-list {
            padding: 0.5rem;
          }

          .message-content {
            max-width: 85%;
          }

          .message-bubble {
            padding: 0.625rem 0.75rem;
          }

          .avatar-user,
          .avatar-assistant {
            width: 32px;
            height: 32px;
            font-size: 0.75rem;
          }
        }
      `}</style>
    </div>
  );
};

MessageList.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      role: PropTypes.oneOf(['user', 'assistant']).isRequired,
      content: PropTypes.string.isRequired,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      sources: PropTypes.arrayOf(
        PropTypes.shape({
          title: PropTypes.string,
          name: PropTypes.string,
          url: PropTypes.string,
        })
      ),
    })
  ),
  isLoading: PropTypes.bool,
};

export { MessageList };