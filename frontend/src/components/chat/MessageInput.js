import React, { useState, useRef } from 'react';
import { useChat } from '../../hooks/useChat';

const MessageInput = ({ disabled = false, placeholder = "Type your message..." }) => {
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef(null);
  const { sendMessage } = useChat();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim() || isSubmitting || disabled) {
      return;
    }

    const messageToSend = message.trim();
    setMessage('');
    setIsSubmitting(true);

    try {
      await sendMessage(messageToSend);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessage(messageToSend);
    } finally {
      setIsSubmitting(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e) => {
    setMessage(e.target.value);
  };

  return (
    <form onSubmit={handleSubmit} className="message-input-form">
      <div className="message-input-container">
        <textarea
          ref={inputRef}
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isSubmitting}
          className="message-input"
          rows={1}
          style={{
            minHeight: '40px',
            maxHeight: '120px',
            resize: 'none',
            overflow: 'auto'
          }}
        />
        <button
          type="submit"
          disabled={!message.trim() || isSubmitting || disabled}
          className="send-button"
        >
          {isSubmitting ? 'Sending...' : 'Send'}
        </button>
      </div>
    </form>
  );
};

export { MessageInput };