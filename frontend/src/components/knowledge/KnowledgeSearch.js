import React, { useState, useEffect } from 'react';
import './KnowledgeSearch.css';

const KnowledgeSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [recentlyAccessed, setRecentlyAccessed] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const filterTags = [
    'Documentation',
    'API Reference',
    'Tutorials',
    'Best Practices',
    'Troubleshooting',
    'Architecture',
    'Security',
    'Performance'
  ];

  useEffect(() => {
    // Load recently accessed items from localStorage
    const recent = JSON.parse(localStorage.getItem('recentKnowledge') || '[]');
    setRecentlyAccessed(recent);
  }, []);

  const handleSearch = async (query = searchQuery) => {
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const mockResults = [
        {
          id: 1,
          title: 'API Authentication Guide',
          snippet: 'Learn how to implement secure authentication in your API endpoints...',
          type: 'Documentation',
          lastUpdated: '2024-01-15'
        },
        {
          id: 2,
          title: 'Database Best Practices',
          snippet: 'Essential guidelines for database design and optimization...',
          type: 'Best Practices',
          lastUpdated: '2024-01-10'
        },
        {
          id: 3,
          title: 'React Performance Tips',
          snippet: 'Optimize your React applications with these proven techniques...',
          type: 'Performance',
          lastUpdated: '2024-01-08'
        }
      ];

      setSearchResults(mockResults);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterToggle = (filter) => {
    setSelectedFilters(prev => 
      prev.includes(filter) 
        ? prev.filter(f => f !== filter)
        : [...prev, filter]
    );
  };

  const handleItemClick = (item) => {
    // Add to recently accessed
    const updated = [item, ...recentlyAccessed.filter(r => r.id !== item.id)].slice(0, 5);
    setRecentlyAccessed(updated);
    localStorage.setItem('recentKnowledge', JSON.stringify(updated));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="knowledge-search">
      <div className="search-header">
        <h1>Knowledge Base</h1>
        <p>Search our comprehensive knowledge repository</p>
      </div>

      <div className="search-section">
        <div className="search-bar-container">
          <div className="search-input-wrapper">
            <input
              type="text"
              className="search-input"
              placeholder="Search travel advisories, safety protocols, destination guides..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button 
              className="search-button"
              onClick={() => handleSearch()}
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="loading-spinner"></div>
              ) : (
                <svg className="search-icon" viewBox="0 0 24 24">
                  <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
              )}
            </button>
          </div>
        </div>

        <div className="filters-section">
          <h3>Filter by Category</h3>
          <div className="filter-tags">
            {filterTags.map(filter => (
              <button
                key={filter}
                className={`filter-tag ${selectedFilters.includes(filter) ? 'active' : ''}`}
                onClick={() => handleFilterToggle(filter)}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="content-section">
        {searchResults.length > 0 && (
          <div className="search-results">
            <h3>Search Results</h3>
            <div className="results-list">
              {searchResults.map(result => (
                <div 
                  key={result.id} 
                  className="result-item"
                  onClick={() => handleItemClick(result)}
                >
                  <div className="result-header">
                    <h4>{result.title}</h4>
                    <span className="result-type">{result.type}</span>
                  </div>
                  <p className="result-snippet">{result.snippet}</p>
                  <div className="result-meta">
                    <span>Last updated: {result.lastUpdated}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="recently-accessed">
          <h3>Recently Accessed</h3>
          {recentlyAccessed.length > 0 ? (
            <div className="recent-list">
              {recentlyAccessed.map(item => (
                <div 
                  key={item.id} 
                  className="recent-item"
                  onClick={() => handleItemClick(item)}
                >
                  <div className="recent-header">
                    <h4>{item.title}</h4>
                    <span className="recent-type">{item.type}</span>
                  </div>
                  <p className="recent-snippet">{item.snippet}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-recent">
              <p>No recently accessed items</p>
            </div>
          )}
        </div>

        <div className="quick-links">
          <h3>Popular Resources</h3>
          <div className="quick-links-grid">
            <div className="quick-link-card">
              <h4>Getting Started</h4>
              <p>New to the platform? Start here for setup and basic concepts.</p>
            </div>
            <div className="quick-link-card">
              <h4>API Documentation</h4>
              <p>Complete reference for all available API endpoints and methods.</p>
            </div>
            <div className="quick-link-card">
              <h4>Best Practices</h4>
              <p>Industry-standard practices and recommended approaches.</p>
            </div>
            <div className="quick-link-card">
              <h4>Troubleshooting</h4>
              <p>Common issues and their solutions to help you resolve problems quickly.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeSearch;