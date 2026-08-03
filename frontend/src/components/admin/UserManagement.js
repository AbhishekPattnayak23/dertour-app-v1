import React, { useState } from 'react';
import '../../../styles/designTokens.css';

const UserManagement = () => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const users = [
    { id: 1, name: 'John Smith', email: 'john.smith@company.com', department: 'Travel Services', role: 'Travel Advisor', lastActive: '2024-01-15', status: 'Active' },
    { id: 2, name: 'Sarah Johnson', email: 'sarah.j@company.com', department: 'Regional Management', role: 'Regional Manager', lastActive: '2024-01-14', status: 'Active' },
    { id: 3, name: 'Mike Chen', email: 'mike.chen@company.com', department: 'Administration', role: 'Admin', lastActive: '2024-01-13', status: 'Inactive' },
    { id: 4, name: 'Lisa Rodriguez', email: 'lisa.r@company.com', department: 'Travel Services', role: 'Travel Advisor', lastActive: '2024-01-12', status: 'Active' },
    { id: 5, name: 'David Wilson', email: 'david.w@company.com', department: 'Regional Management', role: 'Regional Manager', lastActive: '2024-01-11', status: 'Active' }
  ];

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setShowEditModal(true);
  };

  const handleAddNewUser = () => {
    setShowAddModal(true);
  };

  return (
    <div className="user-management-container">
      <div className="user-management-header">
        <h2>User Management</h2>
        <button className="btn-primary" onClick={handleAddNewUser}>
          Add New User
        </button>
      </div>

      <div className="user-table-container">
        <table className="user-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Department</th>
              <th>Role</th>
              <th>Last Active</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{user.department}</td>
                <td>{user.role}</td>
                <td>{user.lastActive}</td>
                <td>
                  <span className={`status-badge ${user.status.toLowerCase()}`}>
                    {user.status}
                  </span>
                </td>
                <td>
                  <button
                    className="btn-edit"
                    onClick={() => handleEditUser(user)}
                  >
                    Edit
                  </button>
                  <button className="btn-deactivate">
                    Deactivate
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit User Modal */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Edit User</h3>
            <div className="form-group">
              <label>Name:</label>
              <input type="text" defaultValue={selectedUser?.name} />
            </div>
            <div className="form-group">
              <label>Email:</label>
              <input type="email" defaultValue={selectedUser?.email} />
            </div>
            <div className="form-group">
              <label>Department:</label>
              <select defaultValue={selectedUser?.department}>
                <option>Travel Services</option>
                <option>Regional Management</option>
                <option>Administration</option>
              </select>
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowEditModal(false)}>Cancel</button>
              <button className="btn-primary">Save Changes</button>
            </div>
          </div>
        </div>
      )}

      {/* Add New User Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Add New User</h3>
            <div className="form-group">
              <label>Name:</label>
              <input type="text" />
            </div>
            <div className="form-group">
              <label>Email:</label>
              <input type="email" />
            </div>
            <div className="form-group">
              <label>Department:</label>
              <select>
                <option>Travel Services</option>
                <option>Regional Management</option>
                <option>Administration</option>
              </select>
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowAddModal(false)}>Cancel</button>
              <button className="btn-primary">Add User</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
