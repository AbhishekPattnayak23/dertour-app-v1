import "../styles/designTokens.css";
import { Button } from "../components/common/Button";
import SearchResults from "../components/knowledge/SearchResults";
import DocumentViewer from "../components/knowledge/DocumentViewer";
import { useSearch } from "../hooks/useSearch";
import React from 'react';
import KnowledgeSearch from '../components/KnowledgeSearch';
import './SearchPage.css';

const SearchPage = () => {
  return (
    <div className="search-page">
      <header className="search-page-header">
        <h1>Travel Knowledge Base</h1>
      </header>
      <main className="search-page-content">
        <KnowledgeSearch />
      </main>
    </div>
  );
};

export default SearchPage;
          <div className="recently-accessed">
      {selectedDocument && (
        <DocumentViewer 
          document={selectedDocument} 
          onClose={() => setSelectedDocument(null)} 
        />
      )}
            <h3>Recently Accessed</h3>
            <div className="recent-documents">
              {mockKnowledgeDocuments.slice(0, 4).map(doc => (
                <div key={doc.id} className="recent-item" onClick={() => setSelectedDocument(doc)}>
                  <div className="recent-title">{doc.title}</div>
                  <div className="recent-type">{doc.type}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
