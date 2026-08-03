// Mock data for conversations and messages with travel-specific content

export const mockConversations = [
  {
    id: "conv-colombia",
    title: "Safety Guidelines - Colombia", 
    messages: [
      {
        id: "msg-c1",
        content: "What safety guidelines should I follow in Colombia?",
        sender: "user",
        timestamp: new Date("2024-01-08T14:00:00Z")
      },
      {
        id: "msg-c2",
        content: "For Colombia, follow standard safety protocols: stay in tourist areas, avoid displaying valuables, and check current regional advisories.",
        sender: "assistant",
        timestamp: new Date("2024-01-08T14:01:00Z"),
        sources: ["Travel Safety Database", "Emergency Protocols"]
      }
    ],
    timestamp: new Date("2024-01-08T14:00:00Z"),
    isActive: false
  },
  {
    id: "conv-morocco",
    title: "Travel Risk Assessment - Morocco",
    messages: [
      {
        id: "msg-m1",
        content: "What are the current travel risks for Morocco?",
        sender: "user",
        timestamp: new Date("2024-01-10T10:00:00Z")
      },
      {
        id: "msg-m2",
        content: "Morocco currently has moderate travel risks. Key considerations include political stability in certain regions and standard health precautions.",
        sender: "assistant",
        timestamp: new Date("2024-01-10T10:01:00Z"),
        sources: ["Country Risk Reports", "Travel Safety Database"]
      }
    ],
    timestamp: new Date("2024-01-10T10:00:00Z"),
    isActive: false
  },
  {
    id: '1',
    title: 'Tokyo Travel Planning',
    lastMessage: 'Best time to visit Tokyo is during spring for cherry blossoms.',
    timestamp: '2024-01-15T14:30:00Z',
    messageCount: 12
  },
  {
    id: '2',
    title: 'European Backpacking Route',
    lastMessage: 'Consider the Eurail pass for cost-effective train travel.',
    timestamp: '2024-01-14T09:15:00Z',
    messageCount: 8
  },
  {
    id: '3',
    title: 'Southeast Asia Budget Guide',
    lastMessage: 'Street food in Thailand is both delicious and affordable.',
    timestamp: '2024-01-13T16:45:00Z',
    messageCount: 15
  },
  {
    id: '4',
    title: 'New York City Weekend',
    lastMessage: 'Book Broadway shows in advance for better seats.',
    timestamp: '2024-01-12T11:20:00Z',
    messageCount: 6
  },
  {
    id: '5',
    title: 'Iceland Road Trip',
    lastMessage: 'The Ring Road offers stunning views of waterfalls and glaciers.',
    timestamp: '2024-01-11T19:30:00Z',
    messageCount: 10
  }
];

export const mockMessages = {
  '1': [
    {
      id: 'm1',
      conversationId: '1',
      content: 'I\'m planning a trip to Tokyo. What\'s the best time to visit?',
      sender: 'user',
      timestamp: '2024-01-15T14:00:00Z'
    },
    {
      id: 'm2',
      conversationId: '1',
      content: 'The best time to visit Tokyo is during spring (March to May) for cherry blossoms or autumn (September to November) for pleasant weather and fall colors. Spring is particularly popular but can be crowded.',
      sender: 'assistant',
      timestamp: '2024-01-15T14:01:30Z',
      sources: [
        { title: 'Japan Tourism Board', url: 'https://www.jnto.go.jp' },
        { title: 'Tokyo Travel Guide', url: 'https://www.timeout.com/tokyo' }
      ]
    },
    {
      id: 'm3',
      conversationId: '1',
      content: 'What are the must-visit attractions in Tokyo?',
      sender: 'user',
      timestamp: '2024-01-15T14:05:00Z'
    },
    {
      id: 'm4',
      conversationId: '1',
      content: 'Here are Tokyo\'s must-visit attractions:\n\n• **Senso-ji Temple** - Tokyo\'s oldest temple in Asakusa\n• **Shibuya Crossing** - World\'s busiest pedestrian crossing\n• **Tokyo Skytree** - Tallest structure in Japan with panoramic views\n• **Meiji Shrine** - Peaceful Shinto shrine in Harajuku\n• **Tsukiji Outer Market** - Fresh seafood and street food\n• **Imperial Palace Gardens** - Beautiful gardens in the city center',
      sender: 'assistant',
      timestamp: '2024-01-15T14:06:45Z',
      sources: [
        { title: 'Lonely Planet Tokyo', url: 'https://www.lonelyplanet.com/japan/tokyo' }
      ]
    },
    {
      id: 'm5',
      conversationId: '1',
      content: 'How much should I budget for a week in Tokyo?',
      sender: 'user',
      timestamp: '2024-01-15T14:28:00Z'
    },
    {
      id: 'm6',
      conversationId: '1',
      content: 'Budget for a week in Tokyo (per person):\n\n**Budget Travel:** $700-1000\n• Hostel: $25-40/night\n• Local food: $20-30/day\n• Public transport: $10/day\n\n**Mid-range:** $1500-2500\n• Business hotel: $80-120/night\n• Mix of restaurants: $50-70/day\n• Activities: $200-300 total\n\n**Luxury:** $3000+\n• High-end hotel: $300+/night\n• Fine dining: $100+/day\n\nTips: Get a JR Pass for trains, eat at convenience stores for cheap meals, and book accommodations early.',
      sender: 'assistant',
      timestamp: '2024-01-15T14:30:00Z',
      sources: [
        { title: 'Budget Your Trip Tokyo', url: 'https://www.budgetyourtrip.com/japan/tokyo' }
      ]
    }
  ],
  '2': [
    {
      id: 'm7',
      conversationId: '2',
      content: 'I want to backpack through Europe for 3 weeks. What route would you recommend?',
      sender: 'user',
      timestamp: '2024-01-14T09:00:00Z'
    },
    {
      id: 'm8',
      conversationId: '2',
      content: 'Here\'s a classic 3-week European backpacking route:\n\n**Week 1: Western Europe**\n• London (2 days) → Paris (3 days) → Amsterdam (2 days)\n\n**Week 2: Central Europe**\n• Berlin (2 days) → Prague (2 days) → Vienna (2 days) → Budapest (1 day)\n\n**Week 3: Southern Europe**\n• Rome (3 days) → Florence (2 days) → Barcelona (2 days)\n\nThis route covers major cities with good train connections. Consider getting a Eurail Pass for flexible train travel.',
      sender: 'assistant',
      timestamp: '2024-01-14T09:02:15Z',
      sources: [
        { title: 'Eurail.com', url: 'https://www.eurail.com' },
        { title: 'Rick Steves Europe', url: 'https://www.ricksteves.com' }
      ]
    },
    {
      id: 'm9',
      conversationId: '2',
      content: 'Is the Eurail pass worth it for this route?',
      sender: 'user',
      timestamp: '2024-01-14T09:10:00Z'
    },
    {
      id: 'm10',
      conversationId: '2',
      content: 'For your 3-week route, a Eurail Pass could be cost-effective:\n\n**21-day Eurail Global Pass:** ~$800\n**Individual tickets estimated:** $600-900\n\n**Pros:**\n• Flexibility to change plans\n• No need to book in advance\n• Covers regional trains too\n• Peace of mind\n\n**Cons:**\n• Reservations still required for high-speed trains\n• May not save money if you take budget flights\n\n**Verdict:** Worth it for the convenience and flexibility, especially for first-time Europe travelers.',
      sender: 'assistant',
      timestamp: '2024-01-14T09:15:00Z',
      sources: [
        { title: 'Eurail Pass Calculator', url: 'https://www.eurail.com/en/eurail-passes' }
      ]
    }
  ],
  '3': [
    {
      id: 'm11',
      conversationId: '3',
      content: 'What\'s a reasonable budget for backpacking Southeast Asia for 2 months?',
      sender: 'user',
      timestamp: '2024-01-13T16:00:00Z'
    },
    {
      id: 'm12',
      conversationId: '3',
      content: 'Southeast Asia is very budget-friendly! Here\'s a 2-month budget breakdown:\n\n**Ultra Budget:** $1,200-1,800\n• Hostel dorms: $5-10/night\n• Street food: $3-8/day\n• Local transport: $2-5/day\n\n**Backpacker Budget:** $2,000-3,000\n• Private room/guesthouse: $10-20/night\n• Mix of street food + restaurants: $8-15/day\n• Occasional flights between countries\n\n**Comfortable Budget:** $3,500-5,000\n• Mid-range hotels: $25-40/night\n• Restaurant meals: $15-25/day\n• Tours and activities: $300-500 total\n\nCountries like Vietnam, Cambodia, and Laos are cheaper than Thailand, Malaysia, and Singapore.',
      sender: 'assistant',
      timestamp: '2024-01-13T16:02:30Z',
      sources: [
        { title: 'Nomadic Matt', url: 'https://www.nomadicmatt.com' },
        { title: 'Price of Travel', url: 'https://www.priceoftravel.com' }
      ]
    },
    {
      id: 'm13',
      conversationId: '3',
      content: 'What about food safety? Any tips for eating street food?',
      sender: 'user',
      timestamp: '2024-01-13T16:40:00Z'
    },
    {
      id: 'm14',
      conversationId: '3',
      content: 'Street food safety tips for Southeast Asia:\n\n**Look for:**\n• High turnover (busy stalls with locals)\n• Food cooked fresh to order\n• Hot, steaming food\n• Clean cooking area\n\n**Avoid:**\n• Pre-cooked food sitting out\n• Raw vegetables/salads initially\n• Ice in drinks (unless from bottled water)\n• Meat that\'s been sitting\n\n**General tips:**\n• Start slowly to adjust your stomach\n• Carry probiotics and anti-diarrheal medicine\n• \"Cook it, peel it, or forget it\"\n• Trust your instincts\n\nStreet food in Thailand is both delicious and affordable - don\'t miss out, just be smart about it!',
      sender: 'assistant',
      timestamp: '2024-01-13T16:45:00Z',
      sources: [
        { title: 'CDC Travel Health', url: 'https://wwwnc.cdc.gov/travel' }
      ]
    }
  ]
};

export const generateMockResponse = (userMessage, conversationId) => {
  const responses = [
    {
      content: `Based on your question about "${userMessage.substring(0, 50)}...", I'd recommend checking the local tourism board for the most up-to-date information. Weather patterns and seasonal events can greatly impact your travel experience.`,
      sources: [
        { title: 'Local Tourism Board', url: 'https://example-tourism.com' },
        { title: 'Travel Weather Guide', url: 'https://weather-travel.com' }
      ]
    },
    {
      content: `That's a great question! For travel planning, I always suggest considering factors like budget, time of year, local customs, and transportation options. Would you like me to elaborate on any of these aspects?`,
      sources: [
        { title: 'Travel Planning Guide', url: 'https://travel-guide.com' },
        { title: 'Cultural Etiquette Tips', url: 'https://culture-guide.com' }
      ]
    },
    {
      content: `Here are some key considerations for your travel plans:\n\n• **Budget**: Plan for unexpected expenses\n• **Documentation**: Check visa requirements\n• **Health**: Consider necessary vaccinations\n• **Insurance**: Get comprehensive travel coverage\n• **Communication**: Download offline maps and translation apps`,
      sources: [
        { title: 'Travel Checklist', url: 'https://travel-checklist.com' },
        { title: 'Visa Requirements Database', url: 'https://visa-info.com' }
      ]
    }
  ];
  
  const randomResponse = responses[Math.floor(Math.random() * responses.length)];
  
  return {
    id: `m${Date.now()}`,
    conversationId,
    content: randomResponse.content,
    sender: 'assistant',
    timestamp: new Date().toISOString(),
    sources: randomResponse.sources
  };
};