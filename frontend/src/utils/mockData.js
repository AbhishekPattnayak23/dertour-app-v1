// Mock data for development and testing

// Mock users data
export const mockUsers = [
  {
    id: 'user-1',
    email: 'john.doe@example.com',
    name: 'John Doe',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
    role: 'traveler',
    preferences: {
      riskTolerance: 'moderate',
      preferredDestinations: ['Europe', 'Asia'],
      travelStyle: 'business',
      notifications: {
        email: true,
        push: true,
        sms: false
      }
    },
    profile: {
      nationality: 'US',
      passportNumber: 'US123456789',
      emergencyContact: {
        name: 'Jane Doe',
        phone: '+1-555-0101',
        relationship: 'spouse'
      },
      medicalInfo: {
        allergies: ['peanuts'],
        medications: [],
        bloodType: 'O+'
      }
    },
    createdAt: '2023-01-15T10:30:00Z',
    lastLogin: '2024-01-15T14:22:00Z'
  },
  {
    id: 'user-2',
    email: 'sarah.wilson@corp.com',
    name: 'Sarah Wilson',
    avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face',
    role: 'admin',
    preferences: {
      riskTolerance: 'low',
      preferredDestinations: ['North America', 'Europe'],
      travelStyle: 'business',
      notifications: {
        email: true,
        push: true,
        sms: true
      }
    },
    profile: {
      nationality: 'CA',
      passportNumber: 'CA987654321',
      emergencyContact: {
        name: 'Michael Wilson',
        phone: '+1-555-0202',
        relationship: 'spouse'
      },
      medicalInfo: {
        allergies: [],
        medications: ['insulin'],
        bloodType: 'A-'
      }
    },
    createdAt: '2022-11-20T09:15:00Z',
    lastLogin: '2024-01-15T16:45:00Z'
  },
  {
    id: 'user-3',
    email: 'alex.chen@example.com',
    name: 'Alex Chen',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
    role: 'traveler',
    preferences: {
      riskTolerance: 'high',
      preferredDestinations: ['Asia', 'South America'],
      travelStyle: 'adventure',
      notifications: {
        email: false,
        push: true,
        sms: false
      }
    },
    profile: {
      nationality: 'AU',
      passportNumber: 'AU456789123',
      emergencyContact: {
        name: 'Lisa Chen',
        phone: '+61-555-0303',
        relationship: 'sister'
      },
      medicalInfo: {
        allergies: ['shellfish'],
        medications: [],
        bloodType: 'B+'
      }
    },
    createdAt: '2023-06-10T12:00:00Z',
    lastLogin: '2024-01-14T20:30:00Z'
  }
];

// Mock conversations data
export const mockConversations = [
  {
    id: 'conv-1',
    userId: 'user-1',
    title: 'Travel to Tokyo - Safety Concerns',
    status: 'active',
    priority: 'medium',
    createdAt: '2024-01-15T09:30:00Z',
    updatedAt: '2024-01-15T14:22:00Z',
    tags: ['japan', 'safety', 'business-travel'],
    messages: [
      {
        id: 'msg-1',
        type: 'user',
        content: 'Hi, I\'m planning a business trip to Tokyo next month. Are there any current safety concerns I should be aware of?',
        timestamp: '2024-01-15T09:30:00Z',
        attachments: []
      },
      {
        id: 'msg-2',
        type: 'ai',
        content: 'Hello! Tokyo is generally very safe for travelers. Currently, there are no major security alerts. However, I recommend staying updated on:\n\n1. Weather conditions (typhoon season)\n2. Current COVID-19 protocols\n3. Emergency contact information\n\nWould you like me to provide specific safety guidelines for your travel dates?',
        timestamp: '2024-01-15T09:32:00Z',
        attachments: [],
        confidence: 0.95
      },
      {
        id: 'msg-3',
        type: 'user',
        content: 'Yes, please. I\'ll be there from February 15-22, 2024.',
        timestamp: '2024-01-15T14:20:00Z',
        attachments: []
      },
      {
        id: 'msg-4',
        type: 'ai',
        content: 'For your February 15-22 travel dates to Tokyo:\n\n✅ **Low Risk Period**: Winter season, no typhoon concerns\n✅ **Weather**: Cool and dry (5-12°C), pack warm clothes\n✅ **Health**: No current health advisories\n\n**Recommendations**:\n- Register with your embassy\n- Keep emergency contacts handy\n- Download Japan Safe Travel app\n\nWould you like me to create a detailed safety checklist for your trip?',
        timestamp: '2024-01-15T14:22:00Z',
        attachments: [],
        confidence: 0.98
      }
    ]
  },
  {
    id: 'conv-2',
    userId: 'user-2',
    title: 'Risk Assessment - Team Trip to Brazil',
    status: 'resolved',
    priority: 'high',
    createdAt: '2024-01-10T11:15:00Z',
    updatedAt: '2024-01-12T16:30:00Z',
    tags: ['brazil', 'team-travel', 'risk-assessment'],
    messages: [
      {
        id: 'msg-5',
        type: 'user',
        content: 'I need a comprehensive risk assessment for our team of 8 traveling to São Paulo and Rio de Janeiro for a conference in March.',
        timestamp: '2024-01-10T11:15:00Z',
        attachments: []
      },
      {
        id: 'msg-6',
        type: 'ai',
        content: 'I\'ll help you create a comprehensive risk assessment for your Brazil team trip. Let me analyze the current situation:\n\n**Security Level**: MEDIUM-HIGH\n**Health Risks**: Moderate\n**Weather**: Rainy season ending\n\nFor a detailed assessment, I\'ll need:\n1. Specific travel dates\n2. Accommodation locations\n3. Conference venue details\n4. Team members\' experience with international travel\n\nShall I start with the preliminary assessment?',
        timestamp: '2024-01-10T11:18:00Z',
        attachments: [],
        confidence: 0.92
      }
    ]
  },
  {
    id: 'conv-3',
    userId: 'user-3',
    title: 'Adventure Travel - Patagonia Safety',
    status: 'active',
    priority: 'high',
    createdAt: '2024-01-14T16:45:00Z',
    updatedAt: '2024-01-14T20:30:00Z',
    tags: ['patagonia', 'adventure', 'hiking', 'emergency-prep'],
    messages: [
      {
        id: 'msg-7',
        type: 'user',
        content: 'Planning a solo hiking trip in Patagonia (both Chile and Argentina sides). What emergency preparations should I make?',
        timestamp: '2024-01-14T16:45:00Z',
        attachments: []
      },
      {
        id: 'msg-8',
        type: 'ai',
        content: 'Patagonia solo hiking requires serious emergency preparation. Here\'s what you need:\n\n🚨 **Critical Safety Measures**:\n- Satellite communication device (InReach/SPOT)\n- Detailed itinerary with local authorities\n- Weather monitoring equipment\n- Emergency shelter and supplies for 72+ hours\n\n**Documentation**:\n- Both Chilean and Argentine permits\n- Comprehensive travel insurance\n- Medical information in Spanish\n\nWhen are you planning to travel? The season significantly impacts safety requirements.',
        timestamp: '2024-01-14T16:48:00Z',
        attachments: [],
        confidence: 0.97
      }
    ]
  }
];

// Mock destinations data
export const mockDestinations = [
  {
    id: 'dest-1',
    name: 'Tokyo',
    country: 'Japan',
    region: 'Asia',
    coordinates: { lat: 35.6762, lng: 139.6503 },
    riskLevel: 'low',
    safetyScore: 9.2,
    lastUpdated: '2024-01-15T08:00:00Z',
    currentAlerts: [],
    weatherCondition: 'clear',
    temperature: { celsius: 8, fahrenheit: 46 },
    currency: 'JPY',
    timeZone: 'Asia/Tokyo',
    languages: ['Japanese'],
    emergencyNumbers: {
      police: '110',
      fire: '119',
      medical: '119'
    },
    embassyInfo: {
      us: {
        address: '1-10-5 Akasaka, Minato-ku, Tokyo 107-8420',
        phone: '+81-3-3224-5000'
      }
    },
    healthInfo: {
      vaccinationsRequired: [],
      vaccinationsRecommended: ['Routine vaccines'],
      healthRisks: ['None significant'],
      medicalFacilities: 'Excellent'
    },
    travelTips: [
      'Very safe for solo travelers',
      'Excellent public transportation',
      'Cash is still preferred in many places',
      'Bowing is a sign of respect'
    ]
  },
  {
    id: 'dest-2',
    name: 'São Paulo',
    country: 'Brazil',
    region: 'South America',
    coordinates: { lat: -23.5505, lng: -46.6333 },
    riskLevel: 'medium-high',
    safetyScore: 6.8,
    lastUpdated: '2024-01-14T12:30:00Z',
    currentAlerts: [
      {
        id: 'alert-1',
        type: 'security',
        level: 'medium',
        title: 'Increased Petty Crime',
        description: 'Higher than usual reports of pickpocketing in tourist areas',
        areas: ['Centro', 'Vila Madalena'],
        validUntil: '2024-02-15T23:59:59Z'
      }
    ],
    weatherCondition: 'rainy',
    temperature: { celsius: 24, fahrenheit: 75 },
    currency: 'BRL',
    timeZone: 'America/Sao_Paulo',
    languages: ['Portuguese'],
    emergencyNumbers: {
      police: '190',
      fire: '193',
      medical: '192'
    },
    embassyInfo: {
      us: {
        address: 'Rua Henri Dunant, 500, Chácara Santo Antônio, São Paulo',
        phone: '+55-11-5186-7000'
      }
    },
    healthInfo: {
      vaccinationsRequired: ['Yellow Fever (if coming from endemic areas)'],
      vaccinationsRecommended: ['Hepatitis A', 'Typhoid', 'Yellow Fever'],
      healthRisks: ['Zika virus', 'Dengue fever'],
      medicalFacilities: 'Good in urban areas'
    },
    travelTips: [
      'Avoid displaying expensive items',
      'Use official taxis or ride-sharing apps',
      'Stay in well-lit areas at night',
      'Learn basic Portuguese phrases'
    ]
  },
  {
    id: 'dest-3',
    name: 'Patagonia',
    country: 'Chile/Argentina',
    region: 'South America',
    coordinates: { lat: -50.3619, lng: -72.2968 },
    riskLevel: 'medium',
    safetyScore: 7.5,
    lastUpdated: '2024-01-13T15:45:00Z',
    currentAlerts: [
      {
        id: 'alert-2',
        type: 'weather',
        level: 'high',
        title: 'Extreme Weather Conditions',
        description: 'Sudden weather changes possible, high winds expected',
        areas: ['Torres del Paine', 'Fitz Roy area'],
        validUntil: '2024-03-31T23:59:59Z'
      }
    ],
    weatherCondition: 'windy',
    temperature: { celsius: 12, fahrenheit: 54 },
    currency: 'CLP/ARS',
    timeZone: 'America/Santiago',
    languages: ['Spanish'],
    emergencyNumbers: {
      chile: { police: '133', fire: '132', medical: '131' },
      argentina: { police: '101', fire: '100', medical: '107' }
    },
    embassyInfo: {
      us_chile: {
        address: 'Av. Andrés Bello 2800, Las Condes, Santiago',
        phone: '+56-2-2330-3000'
      },
      us_argentina: {
        address: 'Av. Colombia 4300, Buenos Aires',
        phone: '+54-11-5777-4533'
      }
    },
    healthInfo: {
      vaccinationsRequired: [],
      vaccinationsRecommended: ['Routine vaccines', 'Hepatitis A'],
      healthRisks: ['Altitude sickness', 'Extreme weather exposure'],
      medicalFacilities: 'Limited in remote areas'
    },
    travelTips: [
      'Always inform someone of your hiking plans',
      'Carry satellite communication device',
      'Pack layers for changing weather',
      'Bring emergency supplies for extended periods'
    ]
  }
];

// Mock risk assessments data
export const mockRiskAssessments = [
  {
    id: 'risk-1',
    userId: 'user-1',
    destinationId: 'dest-1',
    tripId: 'trip-1',
    title: 'Tokyo Business Trip Risk Assessment',
    status: 'completed',
    overallRisk: 'low',
    score: 2.3,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T14:30:00Z',
    validUntil: '2024-02-28T23:59:59Z',
    categories: {
      security: {
        level: 'low',
        score: 1.8,
        factors: [
          'Very low crime rate',
          'Stable political situation',
          'Excellent emergency services'
        ],
        recommendations: [
          'Standard travel precautions sufficient',
          'Keep embassy contact information'
        ]
      },
      health: {
        level: 'low',
        score: 2.1,
        factors: [
          'Excellent healthcare system',
          'No current disease outbreaks',
          'High hygiene standards'
        ],
        recommendations: [
          'Ensure routine vaccines are up to date',
          'Consider travel health insurance'
        ]
      },
      natural: {
        level: 'medium',
        score: 3.2,
        factors: [
          'Earthquake risk',
          'Typhoon season (not applicable for February)',
          'Well-prepared disaster response'
        ],
        recommendations: [
          'Familiarize with earthquake safety procedures',
          'Know evacuation routes from hotel'
        ]
      },
      transportation: {
        level: 'low',
        score: 1.5,
        factors: [
          'World-class public transportation',
          'Excellent road safety',
          'Reliable infrastructure'
        ],
        recommendations: [
          'Use public transportation confidently',
          'Download transportation apps'
        ]
      }
    },
    mitigationPlan: {
      beforeTravel: [
        'Register with embassy',
        'Download safety apps',
        'Share itinerary with contacts',
        'Verify travel insurance coverage'
      ],
      duringTravel: [
        'Keep emergency contacts accessible',
        'Monitor local news and weather',
        'Follow hotel safety instructions',
        'Maintain communication with home base'
      ],
      emergency: [
        'Contact local emergency services (110/119)',
        'Notify embassy if needed',
        'Contact travel insurance provider',
        'Follow evacuation procedures if advised'
      ]
    }
  },
  {
    id: 'risk-2',
    userId: 'user-2',
    destinationId: 'dest-2',
    tripId: 'trip-2',
    title: 'São Paulo Team Conference Risk Assessment',
    status: 'completed',
    overallRisk: 'medium-high',
    score: 6.8,
    createdAt: '2024-01-10T12:00:00Z',
    updatedAt: '2024-01-12T16:30:00Z',
    validUntil: '2024-03-31T23:59:59Z',
    categories: {
      security: {
        level: 'high',
        score: 7.5,
        factors: [
          'Higher crime rates in urban areas',
          'Petty theft and robbery concerns',
          'Political demonstrations possible'
        ],
        recommendations: [
          'Use hotel/venue transportation when possible',
          'Avoid displaying valuables',
          'Stay in groups, especially at night',
          'Use reputable taxi services or ride-sharing'
        ]
      },
      health: {
        level: 'medium',
        score: 5.8,
        factors: [
          'Zika and dengue fever present',
          'Air quality concerns',
          'Food and water safety considerations'
        ],
        recommendations: [
          'Use mosquito repellent',
          'Stick to bottled water and reputable restaurants',
          'Consider hepatitis A vaccination'
        ]
      },
      natural: {
        level: 'low',
        score: 2.3,
        factors: [
          'Low natural disaster risk',
          'Flooding possible during rainy season',
          'Generally stable climate'
        ],
        recommendations: [
          'Monitor weather forecasts',
          'Avoid low-lying areas during heavy rain'
        ]
      },
      transportation: {
        level: 'medium-high',
        score: 6.8,
        factors: [
          'Traffic congestion and accidents',
          'Public transportation safety concerns',
          'Road conditions variable'
        ],
        recommendations: [
          'Use official transportation methods',
          'Allow extra time for travel',
          'Avoid public transport during peak hours'
        ]
      }
    },
    mitigationPlan: {
      beforeTravel: [
        'Brief all team members on safety protocols',
        'Arrange secure transportation',
        'Verify hotel security measures',
        'Establish emergency communication plan'
      ],
      duringTravel: [
        'Daily team check-ins',
        'Group movement when possible',
        'Monitor local security situation',
        'Maintain low profile'
      ],
      emergency: [
        'Contact local emergency services (190/192)',
        'Notify company security immediately',
        'Gather team at designated safe location',
        'Coordinate with embassy if required'
      ]
    }
  },
  {
    id: 'risk-3',
    userId: 'user-3',
    destinationId: 'dest-3',
    tripId: 'trip-3',
    title: 'Patagonia Solo Hiking Risk Assessment',
    status: 'in-progress',
    overallRisk: 'high',
    score: 8.2,
    createdAt: '2024-01-14T17:00:00Z',
    updatedAt: '2024-01-14T20:45:00Z',
    validUntil: '2024-04-30T23:59:59Z',
    categories: {
      security: {
        level: 'low',
        score: 2.8,
        factors: [
          'Low crime rate in remote areas',
          'Border crossing considerations',
          'Rescue service availability'
        ],
        recommendations: [
          'Register with local park authorities',
          'Carry proper identification for both countries',
          'Inform contacts of detailed itinerary'
        ]
      },
      health: {
        level: 'medium',
        score: 6.2,
        factors: [
          'Limited medical facilities in remote areas',
          'Risk of injuries from hiking',
          'Altitude considerations in some areas'
        ],
        recommendations: [
          'Comprehensive first aid training and kit',
          'Evacuation insurance mandatory',
          'Physical fitness assessment before travel'
        ]
      },
      natural: {
        level: 'very-high',
        score: 9.5,
        factors: [
          'Extreme and rapidly changing weather',
          'High winds and storms',
          'Risk of getting lost',
          'Avalanche risk in some areas'
        ],
        recommendations: [
          'Professional weather monitoring equipment',
          'Multiple navigation systems (GPS, compass, maps)',
          'Emergency shelter and extended supplies',
          'Avoid travel during storm warnings'
        ]
      },
      transportation: {
        level: 'medium',
        score: 5.5,
        factors: [
          'Limited access roads',
          'Weather-dependent transportation',
          'Long distances between services'
        ],
        recommendations: [
          'Plan transportation well in advance',
          'Have backup transportation options',
          'Carry spare vehicle supplies if driving'
        ]
      }
    },
    mitigationPlan: {
      beforeTravel: [
        'Complete wilderness first aid course',
        'Test all equipment thoroughly',
        'File detailed trip plans with multiple contacts',
        'Arrange satellite communication device'
      ],
      duringTravel: [
        'Daily check-ins via satellite device',
        'Continuous weather monitoring',
        'Strict adherence to planned routes',
        'Early camp setup before weather changes'
      ],
      emergency: [
        'Activate emergency beacon immediately',
        'Find/create emergency shelter',
        'Conserve resources and stay put if lost',
        'Use pre-arranged emergency signals'
      ]
    }
  }
];

// Mock documents data
export const mockDocuments = [
  {
    id: 'doc-1',
    userId: 'user-1',
    type: 'passport',
    title: 'US Passport',
    fileName: 'passport_john_doe.pdf',
    fileSize: 2048576,
    mimeType: 'application/pdf',
    uploadedAt: '2023-12-15T10:30:00Z',
    expiryDate: '2028-06-15',
    status: 'verified',
    metadata: {
      passportNumber: 'US123456789',
      issuingCountry: 'United States',
      nationality: 'US'
    },
    tags: ['passport', 'identification', 'travel-document']
  },
  {
    id: 'doc-2',
    userId: 'user-1',
    type: 'visa',
    title: 'Japan Tourist Visa',
    fileName: 'japan_visa.pdf',
    fileSize: 1536000,
    mimeType: 'application/pdf',
    uploadedAt: '2024-01-10T14:22:00Z',
    expiryDate: '2024-07-10',
    status: 'verified',
    metadata: {
      visaType: 'tourist',
      destination: 'Japan',
      validFrom: '2024-01-10',
      validUntil: '2024-07-10',
      entries: 'multiple'
    },
    tags: ['visa', 'japan', 'tourist']
  },
  {
    id: 'doc-3',
    userId: 'user-1',
    type: 'insurance',
    title: 'Travel Insurance Policy',
    fileName: 'travel_insurance_2024.pdf',
    fileSize: 3072000,
    mimeType: 'application/pdf',
    uploadedAt: '2024-01-05T09:15:00Z',
    expiryDate: '2024-12-31',
    status: 'verified',
    metadata: {
      policyNumber: 'TRV-2024-001234',
      provider: 'Global Travel Insurance Co.',
      coverage: {
        medical: 1000000,
        evacuation: 500000,
        trip_cancellation: 50000,
        baggage: 5000
      },
      emergencyContact: '+1-800-EMERGENCY'
    },
    tags: ['insurance', 'travel', 'medical-coverage']
  },
  {
    id: 'doc-4',
    userId: 'user-2',
    type: 'passport',
    title: 'Canadian Passport',
    fileName: 'passport_sarah_wilson.pdf',
    fileSize: 1945600,
    mimeType: 'application/pdf',
    uploadedAt: '2023-11-20T11:45:00Z',
    expiryDate: '2029-03-22',
    status: 'verified',
    metadata: {
      passportNumber: 'CA987654321',
      issuingCountry: 'Canada',
      nationality: 'CA'
    },
    tags: ['passport', 'identification', 'travel-document']
  },
  {
    id: 'doc-5',
    userId: 'user-2',
    type: 'vaccination',
    title: 'COVID-19 Vaccination Certificate',
    fileName: 'covid_vaccination.pdf',
    fileSize: 512000,
    mimeType: 'application/pdf',
    uploadedAt: '2023-09-15T16:30:00Z',
    expiryDate: null,
    status: 'verified',
    metadata: {
      vaccinationType: 'COVID-19',
      doses: [
        {
          date: '2021-04-15',
          vaccine: 'Pfizer-BioNTech',
          lot: 'EW0150'
        },
        {
          date: '2021-06-10',
          vaccine: 'Pfizer-BioNTech',
          lot: 'EW0182'
        },
        {
          date: '2023-09-15',
          vaccine: 'Pfizer-BioNTech (Bivalent)',
          lot: 'FG2456'
        }
      ]
    },
    tags: ['vaccination', 'covid-19', 'health-certificate']
  },
  {
    id: 'doc-6',
    userId: 'user-3',
    type: 'passport',
    title: 'Australian Passport',
    fileName: 'passport_alex_chen.pdf',
    fileSize: 2234000,
    mimeType: 'application/pdf',
    uploadedAt: '2023-12-01T13:20:00Z',
    expiryDate: '2030-11-15',
    status: 'verified',
    metadata: {
      passportNumber: 'AU456789123',
      issuingCountry: 'Australia',
      nationality: 'AU'
    },
    tags: ['passport', 'identification', 'travel-document']
  },
  {
    id: 'doc-7',
    userId: 'user-3',
    type: 'emergency',
    title: 'Emergency Contact Information',
    fileName: 'emergency_contacts.pdf',
    fileSize: 256000,
    mimeType: 'application/pdf',
    uploadedAt: '2024-01-12T08:45:00Z',
    expiryDate: null,
    status: 'verified',
    metadata: {
      primaryContact: {
        name: 'Lisa Chen',
        relationship: 'sister',
        phone: '+61-555-0303',
        email: 'lisa.chen@email.com'
      },
      secondaryContact: {
        name: 'David Chen',
        relationship: 'father',
        phone: '+61-555-0404',
        email: 'david.chen@email.com'
      },
      medicalInfo: {
        allergies: ['shellfish'],
        bloodType: 'B+',
        medications: [],
        conditions: []
      }
    },
    tags: ['emergency', 'contacts', 'medical-info']
  },
  {
    id: 'doc-8',
    userId: 'user-1',
    type: 'itinerary',
    title: 'Tokyo Business Trip Itinerary',
    fileName: 'tokyo_itinerary_feb2024.pdf',
    fileSize: 1024000,
    mimeType: 'application/pdf',
    uploadedAt: '2024-01-15T15:00:00Z',
    expiryDate: null,
    status: 'pending',
    metadata: {
      tripDates: {
        departure: '2024-02-15',
        return: '2024-02-22'
      },
      flights: [
        {
          date: '2024-02-15',
          flight: 'UA877',
          departure: 'SFO 11:55',
          arrival: 'NRT 15:20+1'
        },
        {
          date: '2024-02-22',
          flight: 'UA876',
          departure: 'NRT 16:55',
          arrival: 'SFO 09:25'
        }
      ],
      accommodation: {
        name: 'Hotel New Otani Tokyo',
        address: '4-1 Kioi-cho, Chiyoda-ku, Tokyo',
        checkIn: '2024-02-16',
        checkOut: '2024-02-22'
      }
    },
    tags: ['itinerary', 'tokyo', 'business-trip']
  }
];