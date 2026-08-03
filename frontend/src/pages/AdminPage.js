import React, { useState, useEffect } from 'react';
import './AdminPage.css';

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    totalQuestions: 0,
    totalAnswers: 0
  });

  useEffect(() => {
    // Simulate fetching dashboard stats
    setStats({
      totalUsers: 1247,
      activeUsers: 342,
      totalQuestions: 5689,
      totalAnswers: 12453
    });
  }, []);

  return (
    <div className="dashboard-content">
      <h2>Dashboard Overview</h2>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Users</h3>
          <p className="stat-number">{stats.totalUsers}</p>
        </div>
        <div className="stat-card">
          <h3>Active Users</h3>
          <p className="stat-number">{stats.activeUsers}</p>
        </div>
        <div className="stat-card">
          <h3>Total Questions</h3>
          <p className="stat-number">{stats.totalQuestions}</p>
        </div>
        <div className="stat-card">
          <h3>Total Answers</h3>
          <p className="stat-number">{stats.totalAnswers}</p>
        </div>
      </div>
    </div>
  );
};

const UsersManagement = () => {
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Simulate fetching users
    setUsers([
      { id: 1, name: 'John Doe', email: 'john@example.com', role: 'User', status: 'Active' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'Admin', status: 'Active' },
      { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'User', status: 'Inactive' }
    ]);
  }, []);

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleUserAction = (userId, action) => {
    console.log(`Performing ${action} on user ${userId}`);
  };

  return (
    <div className="users-content">
      <h2>User Management</h2>
      <div className="users-controls">
        <input
          type="text"
          placeholder="Search users..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        <button className="btn btn-primary">Add New User</button>
      </div>
      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map(user => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>
                  <span className={`status ${user.status.toLowerCase()}`}>
                    {user.status}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-small"
                    onClick={() => handleUserAction(user.id, 'edit')}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-small btn-danger"
                    onClick={() => handleUserAction(user.id, 'delete')}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const KnowledgeBaseManagement = () => {
  const [articles, setArticles] = useState([]);
  const [newArticle, setNewArticle] = useState({ title: '', content: '' });

  useEffect(() => {
    // Simulate fetching knowledge base articles
    setArticles([
      { id: 1, title: 'How to use the platform', content: 'Step-by-step guide...', status: 'Published' },
      { id: 2, title: 'FAQ', content: 'Frequently asked questions...', status: 'Draft' },
      { id: 3, title: 'Troubleshooting', content: 'Common issues and solutions...', status: 'Published' }
    ]);
  }, []);

  const handleAddArticle = () => {
    if (newArticle.title && newArticle.content) {
      const article = {
        id: Date.now(),
        title: newArticle.title,
        content: newArticle.content,
        status: 'Draft'
      };
      setArticles([...articles, article]);
      setNewArticle({ title: '', content: '' });
    }
  };

  const handleDeleteArticle = (articleId) => {
    setArticles(articles.filter(article => article.id !== articleId));
  };

  return (
    <div className="knowledge-base-content">
      <h2>Knowledge Base Management</h2>
      <div className="add-article-form">
        <h3>Add New Article</h3>
        <input
          type="text"
          placeholder="Article title..."
          value={newArticle.title}
          onChange={(e) => setNewArticle({ ...newArticle, title: e.target.value })}
          className="form-input"
        />
        <textarea
          placeholder="Article content..."
          value={newArticle.content}
          onChange={(e) => setNewArticle({ ...newArticle, content: e.target.value })}
          className="form-textarea"
          rows="4"
        />
        <button className="btn btn-primary" onClick={handleAddArticle}>
          Add Article
        </button>
      </div>
      <div className="articles-list">
        <h3>Existing Articles</h3>
        {articles.map(article => (
          <div key={article.id} className="article-card">
            <h4>{article.title}</h4>
            <p>{article.content.substring(0, 100)}...</p>
            <div className="article-meta">
              <span className={`status ${article.status.toLowerCase()}`}>
                {article.status}
              </span>
              <div className="article-actions">
                <button className="btn btn-small">Edit</button>
                <button
                  className="btn btn-small btn-danger"
                  onClick={() => handleDeleteArticle(article.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState({
    pageViews: 0,
    uniqueVisitors: 0,
    popularQuestions: [],
    userActivity: []
  });

  useEffect(() => {
    // Simulate fetching analytics data
    setAnalyticsData({
      pageViews: 45678,
      uniqueVisitors: 12345,
      popularQuestions: [
        { id: 1, question: 'How to reset password?', views: 234 },
        { id: 2, question: 'How to update profile?', views: 189 },
        { id: 3, question: 'How to delete account?', views: 156 }
      ],
      userActivity: [
        { date: '2023-12-01', users: 45 },
        { date: '2023-12-02', users: 52 },
        { date: '2023-12-03', users: 38 },
        { date: '2023-12-04', users: 67 },
        { date: '2023-12-05', users: 71 }
      ]
    });
  }, []);

  return (
    <div className="analytics-content">
      <h2>Analytics</h2>
      <div className="analytics-stats">
        <div className="stat-card">
          <h3>Page Views</h3>
          <p className="stat-number">{analyticsData.pageViews.toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <h3>Unique Visitors</h3>
          <p className="stat-number">{analyticsData.uniqueVisitors.toLocaleString()}</p>
        </div>
      </div>
      <div className="analytics-sections">
        <div className="popular-questions">
          <h3>Popular Questions</h3>
          <ul>
            {analyticsData.popularQuestions.map(question => (
              <li key={question.id}>
                <span>{question.question}</span>
                <span className="views">{question.views} views</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="user-activity">
          <h3>User Activity (Last 5 Days)</h3>
          <div className="activity-chart">
            {analyticsData.userActivity.map(day => (
              <div key={day.date} className="activity-bar">
                <div className="bar" style={{ height: `${day.users}px` }}></div>
                <span className="date">{day.date}</span>
                <span className="count">{day.users}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const AdminPage = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', component: AdminDashboard },
    { id: 'users', label: 'Users', component: UsersManagement },
    { id: 'knowledge', label: 'Knowledge Base', component: KnowledgeBaseManagement },
    { id: 'analytics', label: 'Analytics', component: Analytics }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || AdminDashboard;

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Admin Panel</h1>
      </div>
      <div className="admin-content">
        <nav className="admin-nav">
          <ul className="tab-list">
            {tabs.map(tab => (
              <li key={tab.id}>
                <button
                  className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
        <main className="admin-main">
          <ActiveComponent />
        </main>
      </div>
    </div>
  );
};

export default AdminPage;