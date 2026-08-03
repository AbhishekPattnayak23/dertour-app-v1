import React from 'react';
import './DocumentViewer.css';

const DocumentViewer = ({ document, isOpen, onClose }) => {
  if (!isOpen || !document) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  React.useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const formatContent = (content) => {
    if (!content) return '';
    
    return content.split('\n').map((paragraph, index) => {
      if (paragraph.trim() === '') return null;
      
      if (paragraph.startsWith('# ')) {
        return <h1 key={index} className="document-h1">{paragraph.substring(2)}</h1>;
      }
      if (paragraph.startsWith('## ')) {
        return <h2 key={index} className="document-h2">{paragraph.substring(3)}</h2>;
      }
      if (paragraph.startsWith('### ')) {
        return <h3 key={index} className="document-h3">{paragraph.substring(4)}</h3>;
      }
      if (paragraph.startsWith('- ') || paragraph.startsWith('* ')) {
        return <li key={index} className="document-list-item">{paragraph.substring(2)}</li>;
      }
      if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
        return <p key={index} className="document-bold">{paragraph.substring(2, paragraph.length - 2)}</p>;
      }
      
      return <p key={index} className="document-paragraph">{paragraph}</p>;
    }).filter(Boolean);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="document-viewer-overlay" onClick={handleOverlayClick}>
      <div className="document-viewer-modal">
        <div className="document-viewer-header">
          <div className="document-viewer-title-section">
            <h2 className="document-viewer-title">{document.title || document.name}</h2>
            <div className="document-viewer-metadata">
              <span className="document-type">{document.type || 'Document'}</span>
              {document.size && <span className="document-size">{formatFileSize(document.size)}</span>}
              {document.createdAt && <span className="document-date">Created: {formatDate(document.createdAt)}</span>}
              {document.updatedAt && <span className="document-date">Modified: {formatDate(document.updatedAt)}</span>}
            </div>
          </div>
          <button 
            className="document-viewer-close"
            onClick={onClose}
            aria-label="Close document viewer"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div className="document-viewer-content">
          {document.description && (
            <div className="document-description">
              <h3>Description</h3>
              <p>{document.description}</p>
            </div>
          )}
          
          {document.tags && document.tags.length > 0 && (
            <div className="document-tags">
              <h4>Tags:</h4>
              <div className="tag-list">
                {document.tags.map((tag, index) => (
                  <span key={index} className="document-tag">{tag}</span>
                ))}
              </div>
            </div>
          )}
          
          <div className="document-main-content">
            {document.content ? (
              <div className="formatted-content">
                {formatContent(document.content)}
              </div>
            ) : (
              <div className="no-content">
                <p>No content available for preview.</p>
                {document.url && (
                  <a 
                    href={document.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="external-link"
                  >
                    Open original document
                  </a>
                )}
              </div>
            )}
          </div>
          
          {document.sections && document.sections.length > 0 && (
            <div className="document-sections">
              <h3>Document Sections</h3>
              {document.sections.map((section, index) => (
                <div key={index} className="document-section">
                  <h4 className="section-title">{section.title || `Section ${index + 1}`}</h4>
                  <div className="section-content">
                    {formatContent(section.content)}
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {document.metadata && Object.keys(document.metadata).length > 0 && (
            <div className="document-metadata-section">
              <h3>Additional Information</h3>
              <dl className="metadata-list">
                {Object.entries(document.metadata).map(([key, value]) => (
                  <div key={key} className="metadata-item">
                    <dt>{key.charAt(0).toUpperCase() + key.slice(1)}:</dt>
                    <dd>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
        
        <div className="document-viewer-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          {document.url && (
            <a 
              href={document.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn-primary"
            >
              Open Original
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;