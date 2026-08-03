import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const AnalyticsDashboard = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('7d');
  const [selectedMetric, setSelectedMetric] = useState('users');

  useEffect(() => {
    fetchAnalyticsData();
  }, [dateRange]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/analytics?range=${dateRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      }
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const mockData = useMemo(() => ({
    userEngagement: [
      { date: '2024-01-01', activeUsers: 1250, newUsers: 85, sessions: 2340 },
      { date: '2024-01-02', activeUsers: 1320, newUsers: 92, sessions: 2450 },
      { date: '2024-01-03', activeUsers: 1180, newUsers: 78, sessions: 2180 },
      { date: '2024-01-04', activeUsers: 1450, newUsers: 110, sessions: 2680 },
      { date: '2024-01-05', activeUsers: 1380, newUsers: 95, sessions: 2520 },
      { date: '2024-01-06', activeUsers: 1520, newUsers: 125, sessions: 2890 },
      { date: '2024-01-07', activeUsers: 1680, newUsers: 140, sessions: 3150 }
    ],
    deviceBreakdown: [
      { name: 'Desktop', value: 45, count: 2250 },
      { name: 'Mobile', value: 35, count: 1750 },
      { name: 'Tablet', value: 20, count: 1000 }
    ],
    pageViews: [
      { page: 'Dashboard', views: 15420, uniqueViews: 8930 },
      { page: 'Profile', views: 12350, uniqueViews: 7820 },
      { page: 'Settings', views: 8940, uniqueViews: 6540 },
      { page: 'Analytics', views: 6780, uniqueViews: 4920 },
      { page: 'Reports', views: 5640, uniqueViews: 4100 }
    ],
    systemUsage: [
      { time: '00:00', cpu: 25, memory: 45, requests: 120 },
      { time: '04:00', cpu: 15, memory: 38, requests: 80 },
      { time: '08:00', cpu: 65, memory: 72, requests: 450 },
      { time: '12:00', cpu: 78, memory: 85, requests: 680 },
      { time: '16:00', cpu: 82, memory: 88, requests: 720 },
      { time: '20:00', cpu: 45, memory: 58, requests: 320 }
    ],
    conversionFunnel: [
      { stage: 'Visitors', count: 10000, percentage: 100 },
      { stage: 'Sign-ups', count: 2500, percentage: 25 },
      { stage: 'Active Users', count: 1800, percentage: 18 },
      { stage: 'Premium Users', count: 450, percentage: 4.5 }
    ]
  }), []);

  const data = analyticsData || mockData;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const StatCard = ({ title, value, change, color = 'blue' }) => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`text-sm font-medium ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {change >= 0 ? '+' : ''}{change}%
        </div>
      </div>
    </div>
  );

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900">{`${label}`}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.dataKey}: ${entry.value.toLocaleString()}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Monitor user engagement and system performance</p>
        </div>
        <div className="flex space-x-2 mt-4 sm:mt-0">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1d">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <button
            onClick={fetchAnalyticsData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Users"
          value="1,680"
          change={12.5}
        />
        <StatCard
          title="New Signups"
          value="140"
          change={8.3}
        />
        <StatCard
          title="Total Sessions"
          value="3,150"
          change={15.7}
        />
        <StatCard
          title="Conversion Rate"
          value="4.5%"
          change={-2.1}
        />
      </div>

      {/* User Engagement Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-900">User Engagement Trends</h2>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="users">Active Users</option>
            <option value="sessions">Sessions</option>
            <option value="newUsers">New Users</option>
          </select>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data.userEngagement}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tickFormatter={(value) => new Date(value).toLocaleDateString()}
            />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey={selectedMetric === 'users' ? 'activeUsers' : selectedMetric === 'sessions' ? 'sessions' : 'newUsers'}
              stroke="#0088FE"
              fill="#0088FE"
              fillOpacity={0.3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Breakdown */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Device Breakdown</h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data.deviceBreakdown}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percentage }) => `${name}: ${percentage}%`}
              >
                {data.deviceBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Pages */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Top Pages</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.pageViews} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="page" type="category" width={80} />
              <Tooltip />
              <Bar dataKey="views" fill="#0088FE" />
              <Bar dataKey="uniqueViews" fill="#00C49F" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Performance */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">System Performance</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.systemUsage}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="cpu"
              stroke="#FF8042"
              strokeWidth={2}
              name="CPU Usage (%)"
            />
            <Line
              type="monotone"
              dataKey="memory"
              stroke="#0088FE"
              strokeWidth={2}
              name="Memory Usage (%)"
            />
            <Line
              type="monotone"
              dataKey="requests"
              stroke="#00C49F"
              strokeWidth={2}
              name="Requests/min"
              yAxisId="right"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Conversion Funnel */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Conversion Funnel</h2>
        <div className="space-y-4">
          {data.conversionFunnel.map((stage, index) => (
            <div key={stage.stage} className="flex items-center space-x-4">
              <div className="w-24 text-sm font-medium text-gray-700">{stage.stage}</div>
              <div className="flex-1">
                <div className="bg-gray-200 rounded-full h-6 relative overflow-hidden">
                  <div
                    className="bg-blue-600 h-full rounded-full transition-all duration-300"
                    style={{ width: `${stage.percentage}%` }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white">
                    {stage.count.toLocaleString()} ({stage.percentage}%)
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Real-time Activity Feed */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Recent Activity</h2>
        <div className="space-y-3">
          {[
            { time: '2 min ago', event: 'New user registration', user: 'john.doe@example.com' },
            { time: '5 min ago', event: 'Premium subscription', user: 'jane.smith@example.com' },
            { time: '8 min ago', event: 'File upload', user: 'mike.wilson@example.com' },
            { time: '12 min ago', event: 'Password reset', user: 'sarah.jones@example.com' },
            { time: '15 min ago', event: 'Profile update', user: 'david.brown@example.com' }
          ].map((activity, index) => (
            <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{activity.event}</p>
                <p className="text-xs text-gray-600">{activity.user}</p>
              </div>
              <span className="text-xs text-gray-500">{activity.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;