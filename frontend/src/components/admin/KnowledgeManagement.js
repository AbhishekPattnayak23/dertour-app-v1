import React, { useState, useEffect, useRef } from 'react';
import './KnowledgeManagement.css';

const DocumentUploadModal = ({ isOpen, onClose, onUpload }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('documents', file);
      });
      
      await onUpload(formData);
      setFiles([]);
      onClose();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Upload Documents</h2>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>
        
        <div className="modal-body">
          <div 
            className={`drop-zone ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="drop-zone-content">
              <div className="upload-icon">📁</div>
              <p>Drag and drop files here or click to select</p>
              <p className="file-types">Supported: PDF, DOC, DOCX, TXT</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>

          {files.length > 0 && (
            <div className="selected-files">
              <h3>Selected Files ({files.length})</h3>
              <div className="file-list">
                {files.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{formatFileSize(file.size)}</span>
                    </div>
                    <button 
                      className="remove-file"
                      onClick={() => removeFile(index)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button 
            className="btn-primary" 
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
          >
            {uploading ? 'Uploading...' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
};

const KnowledgeManagement = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortField, setSortField] = useState('uploadedAt');
  const [sortDirection, setSortDirection] = useState('desc');
  const [selectedDocuments, setSelectedDocuments] = useState([]);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/documents');
      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (formData) => {
    const response = await fetch('/api/admin/documents/upload', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Upload failed');
    }
    
    await fetchDocuments();
  };

  const handleDelete = async (documentIds) => {
    if (!window.confirm(`Delete ${documentIds.length} document(s)?`)) return;
    
    try {
      await fetch('/api/admin/documents/delete', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ids: documentIds }),
      });
      
      setSelectedDocuments([]);
      await fetchDocuments();
    } catch (error) {
      console.error('Failed to delete documents:', error);
    }
  };

  const handleReprocess = async (documentIds) => {
    try {
      await fetch('/api/admin/documents/reprocess', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ids: documentIds }),
      });
      
      setSelectedDocuments([]);
      await fetchDocuments();
    } catch (error) {
      console.error('Failed to reprocess documents:', error);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredAndSortedDocuments = documents
    .filter(doc => {
      const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || doc.status === filterStatus;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      const direction = sortDirection === 'asc' ? 1 : -1;
      
      if (aValue < bValue) return -1 * direction;
      if (aValue > bValue) return 1 * direction;
      return 0;
    });

  const handleSelectDocument = (documentId) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId)
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleSelectAll = () => {
    if (selectedDocuments.length === filteredAndSortedDocuments.length) {
      setSelectedDocuments([]);
    } else {
      setSelectedDocuments(filteredAndSortedDocuments.map(doc => doc.id));
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      processing: 'status-processing',
      completed: 'status-completed',
      failed: 'status-failed',
      pending: 'status-pending'
    };
    
    return <span className={`status-badge ${statusClasses[status]}`}>{status}</span>;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="knowledge-management">
      <div className="page-header">
        <h1>Knowledge Management</h1>
        <button 
          className="btn-primary"
          onClick={() => setIsUploadModalOpen(true)}
        >
          Upload Documents
        </button>
      </div>

      <div className="controls-section">
        <div className="search-filter-controls">
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {selectedDocuments.length > 0 && (
          <div className="bulk-actions">
            <span>{selectedDocuments.length} selected</span>
            <button 
              className="btn-secondary"
              onClick={() => handleReprocess(selectedDocuments)}
            >
              Reprocess
            </button>
            <button 
              className="btn-danger"
              onClick={() => handleDelete(selectedDocuments)}
            >
              Delete
            </button>
          </div>
        )}
      </div>

      <div className="documents-table-container">
        {loading ? (
          <div className="loading">Loading documents...</div>
        ) : (
          <table className="documents-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedDocuments.length === filteredAndSortedDocuments.length && filteredAndSortedDocuments.length > 0}
                    onChange={handleSelectAll}
                  />
                </th>
                <th 
                  onClick={() => handleSort('name')}
                  className="sortable"
                >
                  Name {sortField === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  onClick={() => handleSort('status')}
                  className="sortable"
                >
                  Status {sortField === 'status' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  onClick={() => handleSort('size')}
                  className="sortable"
                >
                  Size {sortField === 'size' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  onClick={() => handleSort('uploadedAt')}
                  className="sortable"
                >
                  Uploaded {sortField === 'uploadedAt' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAndSortedDocuments.map(document => (
                <tr key={document.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedDocuments.includes(document.id)}
                      onChange={() => handleSelectDocument(document.id)}
                    />
                  </td>
                  <td className="document-name">
                    <div>
                      <span className="name">{document.name}</span>
                      <span className="type">{document.type}</span>
                    </div>
                  </td>
                  <td>{getStatusBadge(document.status)}</td>
                  <td>{document.size}</td>
                  <td>{formatDate(document.uploadedAt)}</td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="btn-small btn-secondary"
                        onClick={() => handleReprocess([document.id])}
                      >
                        Reprocess
                      </button>
                      <button 
                        className="btn-small btn-danger"
                        onClick={() => handleDelete([document.id])}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && filteredAndSortedDocuments.length === 0 && (
          <div className="empty-state">
            <p>No documents found</p>
          </div>
        )}
      </div>

      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={handleUpload}
      />
    </div>
  );
};

export default KnowledgeManagement;
export { DocumentUploadModal };