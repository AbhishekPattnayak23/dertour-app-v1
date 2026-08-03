import { useState, useCallback, useRef } from 'react';

const useChat = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const messageIdCounter = useRef(0);
  const conversationIdCounter = useRef(0);

  const generateMessageId = () => {
    messageIdCounter.current += 1;
    return `msg_${messageIdCounter.current}_${Date.now()}`;
  };

  const generateConversationId = () => {
    conversationIdCounter.current += 1;
    return `conv_${conversationIdCounter.current}_${Date.now()}`;
  };

  const mockAiResponses = [
    "I understand your question. Let me help you with that.",
    "That's an interesting point. Here's what I think about it.",
    "Based on what you've shared, I would suggest the following approach.",
    "Great question! Let me break this down for you.",
    "I see what you're looking for. Here's a comprehensive answer.",
    "Thanks for asking! This is something I can definitely help with.",
    "Let me provide you with some insights on this topic.",
    "That's a common question, and here's how I would approach it."
  ];

  const generateMockAiResponse = useCallback(() => {
    const randomIndex = Math.floor(Math.random() * mockAiResponses.length);
    return mockAiResponses[randomIndex];
  }, []);

  const createNewConversation = useCallback(() => {
    const newConversationId = generateConversationId();
    const newConversation = {
      id: newConversationId,
      title: 'New Conversation',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    setConversations(prev => [newConversation, ...prev]);
    setActiveConversationId(newConversationId);
    
    return newConversationId;
  }, []);

  const switchConversation = useCallback((conversationId) => {
    setActiveConversationId(conversationId);
  }, []);

  const updateConversationTitle = useCallback((conversationId, newTitle) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? { ...conv, title: newTitle, updatedAt: new Date().toISOString() }
          : conv
      )
    );
  }, []);

  const deleteConversation = useCallback((conversationId) => {
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));
    
    if (activeConversationId === conversationId) {
      const remainingConversations = conversations.filter(conv => conv.id !== conversationId);
      if (remainingConversations.length > 0) {
        setActiveConversationId(remainingConversations[0].id);
      } else {
        setActiveConversationId(null);
      }
    }
  }, [activeConversationId, conversations]);

  const addMessageToConversation = useCallback((conversationId, message) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? { 
              ...conv, 
              messages: [...conv.messages, message],
              updatedAt: new Date().toISOString(),
              title: conv.messages.length === 0 ? message.content.substring(0, 30) + '...' : conv.title
            }
          : conv
      )
    );
  }, []);

  const sendMessage = useCallback(async (content, conversationId = null) => {
    if (!content.trim()) return;

    setIsLoading(true);

    try {
      let targetConversationId = conversationId || activeConversationId;
      
      if (!targetConversationId) {
        targetConversationId = createNewConversation();
      }

      const userMessage = {
        id: generateMessageId(),
        content: content.trim(),
        sender: 'user',
        timestamp: new Date().toISOString()
      };

      addMessageToConversation(targetConversationId, userMessage);

      setTimeout(() => {
        const aiResponse = {
          id: generateMessageId(),
          content: generateMockAiResponse(),
          sender: 'ai',
          timestamp: new Date().toISOString()
        };

        addMessageToConversation(targetConversationId, aiResponse);
        setIsLoading(false);
      }, 1000 + Math.random() * 2000);

    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
    }
  }, [activeConversationId, createNewConversation, addMessageToConversation, generateMockAiResponse]);

  const clearConversation = useCallback((conversationId) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? { 
              ...conv, 
              messages: [],
              title: 'New Conversation',
              updatedAt: new Date().toISOString()
            }
          : conv
      )
    );
  }, []);

  const getActiveConversation = useCallback(() => {
    if (!activeConversationId) return null;
    return conversations.find(conv => conv.id === activeConversationId) || null;
  }, [activeConversationId, conversations]);

  const getConversationById = useCallback((conversationId) => {
    return conversations.find(conv => conv.id === conversationId) || null;
  }, [conversations]);

  return {
    conversations,
    activeConversationId,
    isLoading,
    activeConversation: getActiveConversation(),
    createNewConversation,
    switchConversation,
    sendMessage,
    updateConversationTitle,
    deleteConversation,
    clearConversation,
    getConversationById
  };
};

export { useChat };