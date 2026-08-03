import React from 'react';
import '../../../styles/designTokens.css';

const Dashboard = () => {
  const kpiData = [
    { title: 'Active Users', value: '387', trend: '+12%' },
    { title: 'Conversations This Week', value: '1,247', trend: '+8%' },
    { title: 'User Satisfaction', value: '89%', trend: '+3%' },
    { title: 'Documents Available', value: '156', trend: '+5%' }
  ];

  const queryCategories = [
    { name: 'Risk Assessments', percentage: 45, color: '#2563eb' },
    { name: 'Safety Guidelines', percentage: 30, color: '#dc2626' },
    { name: 'General Info', percentage: 25, color: '#059669' }
  ];

  const usageData = [
    { day: 'Mon', conversations: 145 },
    { day: 'Tue', conversations: 189 },
    { day: 'Wed', conversations: 167 },
    { day: 'Thu', conversations: 203 },
    { day: 'Fri', conversations: 178 },
    { day: 'Sat', conversations: 98 },
    { day: 'Sun', conversations: 123 }
  ];

  return (
    <div className="dashboard-container">
      <h2>Dashboard Overview</h2>

      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpiData.map((kpi, index) => (
          <div key={index} className="kpi-card">
            <h3>{kpi.title}</h3>
            <div className="kpi-value">{kpi.value}</div>
            <div className="kpi-trend">{kpi.trend}</div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        <div className="chart-container">
          <h3>Daily Usage (Past 7 Days)</h3>
          <div className="bar-chart">
            {usageData.map((data, index) => (
              <div key={index} className="bar-item">
                <div
                  className="bar"
                  style={{height: `${(data.conversations / 250) * 100}%`}}
                ></div>
                <span>{data.day}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-container">
          <h3>Query Categories</h3>
          <div className="pie-chart-legend">
            {queryCategories.map((category, index) => (
              <div key={index} className="legend-item">
                <div
                  className="legend-color"
                  style={{backgroundColor: category.color}}
                ></div>
                <span>{category.name}: {category.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
