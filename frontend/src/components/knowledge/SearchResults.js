import React from 'react';
import PropTypes from 'prop-types';
import './SearchResults.css';

const SearchResults = ({ results = [], onDocumentClick, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="search-results">
        <div className="search-results__loading">
          <div className="spinner"></div>
          <p>Searching documents...</p>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="search-results">
        <div className="search-results__empty">
          <p>No documents found. Try adjusting your search terms.</p>
        </div>
      </div>
    );
  }

  const handleCardClick = (document) => {
    if (onDocumentClick) {
      onDocumentClick(document);
    }
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      return 'Unknown date';
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      pdf: '#e74c3c',
      doc: '#3498db',
      docx: '#3498db',
      txt: '#95a5a6',
      md: '#f39c12',
      default: '#7f8c8d'
    };
    return colors[type?.toLowerCase()] || colors.default;
  };

  const truncateText = (text, maxLength = 200) => {
    if (!text || text.length <= maxLength) {
      return text || '';
    }
    return text.substring(0, maxLength).trim() + '...';
  };

  return (
    <div className="search-results">
      <div className="search-results__header">
        <h3>Search Results ({results.length})</h3>
      </div>
      
      <div className="search-results__grid">
        {results.map((document, index) => (
          <div
            key={document.id || index}
            className="document-card"
            onClick={() => handleCardClick(document)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleCardClick(document);
              }
            }}
          >
            <div className="document-card__header">
              <h4 className="document-card__title" title={document.title}>
                {document.title || 'Untitled Document'}
              </h4>
              <span
                className="document-card__type-badge"
                style={{ backgroundColor: getTypeColor(document.type) }}
              >
                {document.type?.toUpperCase() || 'DOC'}
              </span>
            </div>
            
            <div className="document-card__meta">
              <span className="document-card__date">
                {formatDate(document.created_at || document.modified_at)}
              </span>
              {document.size && (
                <span className="document-card__size">
                  {(document.size / 1024).toFixed(1)} KB
                </span>
              )}
            </div>
            
            <div className="document-card__content">
              <p className="document-card__excerpt">
                {truncateText(document.excerpt || document.content || document.description)}
              </p>
            </div>
            
            {document.tags && document.tags.length > 0 && (
              <div className="document-card__tags">
                {document.tags.slice(0, 3).map((tag, tagIndex) => (
                  <span key={tagIndex} className="document-card__tag">
                    {tag}
                  </span>
                ))}
                {document.tags.length > 3 && (
                  <span className="document-card__tag-more">
                    +{document.tags.length - 3} more
                  </span>
                )}
              </div>
            )}
            
            <div className="document-card__footer">
              <span className="document-card__click-hint">
                Click to open
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

SearchResults.propTypes = {
  results: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      title: PropTypes.string,
      type: PropTypes.string,
      created_at: PropTypes.string,
      modified_at: PropTypes.string,
      size: PropTypes.number,
      excerpt: PropTypes.string,
      content: PropTypes.string,
      description: PropTypes.string,
      tags: PropTypes.arrayOf(PropTypes.string)
    })
  ),
  onDocumentClick: PropTypes.func,
  isLoading: PropTypes.bool
};

export default SearchResults;