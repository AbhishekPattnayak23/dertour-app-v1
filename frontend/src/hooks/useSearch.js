import { useState, useEffect, useMemo, useCallback } from 'react';

export const useSearch = (documents = [], options = {}) => {
  const {
    searchFields = ['title', 'content', 'tags'],
    debounceMs = 300,
    caseSensitive = false,
    exactMatch = false,
    minSearchLength = 1
  } = options;

  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    tags: [],
    dateRange: { start: null, end: null },
    author: '',
    status: ''
  });
  const [sortBy, setSortBy] = useState('relevance');
  const [sortOrder, setSortOrder] = useState('desc');
  const [isLoading, setIsLoading] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce search query
  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
      setIsLoading(false);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [searchQuery, debounceMs]);

  // Search function
  const searchDocuments = useCallback((docs, query) => {
    if (!query || query.length < minSearchLength) {
      return docs;
    }

    const searchTerm = caseSensitive ? query : query.toLowerCase();
    
    return docs.filter(doc => {
      return searchFields.some(field => {
        const fieldValue = doc[field];
        if (!fieldValue) return false;

        let searchableValue;
        if (Array.isArray(fieldValue)) {
          searchableValue = fieldValue.join(' ');
        } else {
          searchableValue = String(fieldValue);
        }

        if (!caseSensitive) {
          searchableValue = searchableValue.toLowerCase();
        }

        if (exactMatch) {
          return searchableValue === searchTerm;
        } else {
          return searchableValue.includes(searchTerm);
        }
      });
    });
  }, [searchFields, caseSensitive, exactMatch, minSearchLength]);

  // Apply filters
  const applyFilters = useCallback((docs) => {
    return docs.filter(doc => {
      // Category filter
      if (filters.category && doc.category !== filters.category) {
        return false;
      }

      // Tags filter
      if (filters.tags.length > 0) {
        const docTags = doc.tags || [];
        const hasMatchingTag = filters.tags.some(tag => 
          docTags.includes(tag)
        );
        if (!hasMatchingTag) return false;
      }

      // Date range filter
      if (filters.dateRange.start || filters.dateRange.end) {
        const docDate = new Date(doc.createdAt || doc.updatedAt);
        if (filters.dateRange.start && docDate < new Date(filters.dateRange.start)) {
          return false;
        }
        if (filters.dateRange.end && docDate > new Date(filters.dateRange.end)) {
          return false;
        }
      }

      // Author filter
      if (filters.author && doc.author !== filters.author) {
        return false;
      }

      // Status filter
      if (filters.status && doc.status !== filters.status) {
        return false;
      }

      return true;
    });
  }, [filters]);

  // Sort documents
  const sortDocuments = useCallback((docs) => {
    const sortedDocs = [...docs].sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'title':
          comparison = (a.title || '').localeCompare(b.title || '');
          break;
        case 'date':
          comparison = new Date(a.createdAt || 0) - new Date(b.createdAt || 0);
          break;
        case 'updatedAt':
          comparison = new Date(a.updatedAt || 0) - new Date(b.updatedAt || 0);
          break;
        case 'author':
          comparison = (a.author || '').localeCompare(b.author || '');
          break;
        case 'category':
          comparison = (a.category || '').localeCompare(b.category || '');
          break;
        case 'relevance':
        default:
          // Calculate relevance score based on search query
          if (debouncedQuery) {
            const scoreA = calculateRelevanceScore(a, debouncedQuery);
            const scoreB = calculateRelevanceScore(b, debouncedQuery);
            comparison = scoreB - scoreA;
          } else {
            comparison = new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0);
          }
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return sortedDocs;
  }, [sortBy, sortOrder, debouncedQuery]);

  // Calculate relevance score for search results
  const calculateRelevanceScore = useCallback((doc, query) => {
    let score = 0;
    const searchTerm = caseSensitive ? query : query.toLowerCase();

    searchFields.forEach((field, index) => {
      const fieldValue = doc[field];
      if (!fieldValue) return;

      let searchableValue;
      if (Array.isArray(fieldValue)) {
        searchableValue = fieldValue.join(' ');
      } else {
        searchableValue = String(fieldValue);
      }

      if (!caseSensitive) {
        searchableValue = searchableValue.toLowerCase();
      }

      // Higher weight for title matches
      const fieldWeight = field === 'title' ? 3 : field === 'tags' ? 2 : 1;
      
      // Exact match gets highest score
      if (searchableValue === searchTerm) {
        score += 10 * fieldWeight;
      }
      // Starts with search term gets high score
      else if (searchableValue.startsWith(searchTerm)) {
        score += 5 * fieldWeight;
      }
      // Contains search term gets lower score
      else if (searchableValue.includes(searchTerm)) {
        score += 2 * fieldWeight;
      }
    });

    return score;
  }, [searchFields, caseSensitive]);

  // Process documents with search, filter, and sort
  const processedDocuments = useMemo(() => {
    let result = documents;
    
    // Apply search
    result = searchDocuments(result, debouncedQuery);
    
    // Apply filters
    result = applyFilters(result);
    
    // Apply sorting
    result = sortDocuments(result);
    
    return result;
  }, [documents, debouncedQuery, searchDocuments, applyFilters, sortDocuments]);

  // Helper functions
  const updateFilter = useCallback((filterKey, value) => {
    setFilters(prev => ({
      ...prev,
      [filterKey]: value
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      category: '',
      tags: [],
      dateRange: { start: null, end: null },
      author: '',
      status: ''
    });
  }, []);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  const clearAll = useCallback(() => {
    clearSearch();
    clearFilters();
  }, [clearSearch, clearFilters]);

  const hasActiveFilters = useMemo(() => {
    return filters.category || 
           filters.tags.length > 0 || 
           filters.dateRange.start || 
           filters.dateRange.end || 
           filters.author || 
           filters.status;
  }, [filters]);

  const hasActiveSearch = Boolean(debouncedQuery && debouncedQuery.length >= minSearchLength);

  const resultsCount = processedDocuments.length;
  const totalCount = documents.length;

  return {
    // Search state
    searchQuery,
    setSearchQuery,
    debouncedQuery,
    
    // Filter state
    filters,
    setFilters,
    updateFilter,
    
    // Sort state
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    
    // Results
    results: processedDocuments,
    resultsCount,
    totalCount,
    
    // Status
    isLoading,
    hasActiveFilters,
    hasActiveSearch,
    
    // Actions
    clearFilters,
    clearSearch,
    clearAll
  };
};