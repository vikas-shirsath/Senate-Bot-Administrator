import { useState, useEffect, useCallback } from "react";
import {
  Users, FileText, BarChart3, LogOut, CheckCircle, XCircle,
  Clock, ChevronRight, MessageSquare, ArrowLeft, RefreshCw,
  Shield, Eye,
} from "lucide-react";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import "./AdminPanel.css";

const API_BASE = "http://localhost:8000";

export default function AdminPanel({ getToken, onLogout, userName }) {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [users, setUsers] = useState([]);
  const [serviceRequests, setServiceRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userMessages, setUserMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const authHeaders = useCallback(async () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${await getToken()}`,
  }), [getToken]);

  // ── Fetch users ──────────
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const h = await authHeaders();
      const resp = await fetch(`${API_BASE}/admin/users`, { headers: h });
      setUsers(await resp.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [authHeaders]);

  // ── Fetch all service requests ──────────
  const fetchRequests = useCallback(async () => {
    setLoading(true);
    try {
      const h = await authHeaders();
      const resp = await fetch(`${API_BASE}/admin/service-requests`, { headers: h });
      setServiceRequests(await resp.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [authHeaders]);

  // ── Update service request status ──────────
  const updateStatus = async (id, status) => {
    try {
      const h = await authHeaders();
      await fetch(`${API_BASE}/admin/service-requests/${id}`, {
        method: "PATCH", headers: h,
        body: JSON.stringify({ status }),
      });
      fetchRequests();
    } catch (e) { console.error(e); }
  };

  // ── View user messages ──────────
  const viewUserMessages = async (userId) => {
    setLoadingMessages(true);
    setSelectedUser(userId);
    try {
      const h = await authHeaders();
      const resp = await fetch(`${API_BASE}/admin/users/${userId}/messages`, { headers: h });
      setUserMessages(await resp.json());
    } catch (e) { console.error(e); }
    finally { setLoadingMessages(false); }
  };

  useEffect(() => {
    if (activeTab === "users") fetchUsers();
    if (activeTab === "requests") fetchRequests();
  }, [activeTab, fetchUsers, fetchRequests]);

  const formatDate = (d) => new Date(d).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });

  const formatServiceName = (s) =>
    (s || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  const TABS = [
    { id: "dashboard", label: "Analytics", icon: <BarChart3 size={16} /> },
    { id: "users", label: "Users", icon: <Users size={16} /> },
    { id: "requests", label: "Service Requests", icon: <FileText size={16} /> },
  ];

  return (
    <div className="admin-layout">
      {/* Sidebar */}
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <Shield size={20} />
          <div>
            <h2>Senate Admin</h2>
            <span className="admin-role-tag">Administrator</span>
          </div>
        </div>

        <nav className="admin-nav">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`admin-nav-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => { setActiveTab(tab.id); setSelectedUser(null); }}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="admin-sidebar-footer">
          <div className="admin-user-info">
            <span className="admin-user-avatar">{userName.charAt(0).toUpperCase()}</span>
            <span className="admin-user-name">{userName}</span>
          </div>
          <button className="admin-logout-btn" onClick={onLogout}>
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="admin-main">
        {activeTab === "dashboard" && (
          <AnalyticsDashboard
            getToken={getToken}
            onBack={() => {}}
          />
        )}

        {activeTab === "users" && (
          <div className="admin-content">
            <div className="admin-content-header">
              {selectedUser ? (
                <>
                  <button className="admin-back-btn" onClick={() => setSelectedUser(null)}>
                    <ArrowLeft size={16} />
                  </button>
                  <h2>User Messages</h2>
                </>
              ) : (
                <>
                  <h2><Users size={20} /> All Users</h2>
                  <button className="admin-refresh-btn" onClick={fetchUsers} disabled={loading}>
                    <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
                  </button>
                </>
              )}
            </div>

            {selectedUser ? (
              /* User messages view */
              <div className="admin-messages-view">
                {loadingMessages ? (
                  <div className="admin-loading">Loading messages…</div>
                ) : userMessages.length === 0 ? (
                  <div className="admin-empty">No messages found for this user.</div>
                ) : (
                  <div className="admin-messages-list">
                    {userMessages.map((msg, i) => (
                      <div key={i} className={`admin-msg ${msg.role}`}>
                        <div className="admin-msg-header">
                          <span className={`admin-msg-role ${msg.role}`}>
                            {msg.role === "user" ? "👤 User" : "🏛️ Bot"}
                          </span>
                          <span className="admin-msg-time">{formatDate(msg.created_at)}</span>
                          {msg.original_language && (
                            <span className="admin-msg-lang">{msg.original_language.toUpperCase()}</span>
                          )}
                        </div>
                        <div className="admin-msg-content">{msg.content}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              /* Users table */
              <div className="admin-table-wrap">
                {loading ? (
                  <div className="admin-loading">Loading users…</div>
                ) : (
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Joined</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map(u => (
                        <tr key={u.id}>
                          <td className="user-name-cell">
                            <span className="user-table-avatar">
                              {(u.name || u.email || "?").charAt(0).toUpperCase()}
                            </span>
                            {u.name || "—"}
                          </td>
                          <td>{u.email}</td>
                          <td>
                            <span className={`role-badge ${u.role || "user"}`}>
                              {(u.role || "user").toUpperCase()}
                            </span>
                          </td>
                          <td>{formatDate(u.created_at)}</td>
                          <td>
                            <button className="admin-action-btn" onClick={() => viewUserMessages(u.id)}>
                              <Eye size={13} /> View Messages
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === "requests" && (
          <div className="admin-content">
            <div className="admin-content-header">
              <h2><FileText size={20} /> Service Requests</h2>
              <button className="admin-refresh-btn" onClick={fetchRequests} disabled={loading}>
                <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
              </button>
            </div>

            <div className="admin-table-wrap">
              {loading ? (
                <div className="admin-loading">Loading requests…</div>
              ) : serviceRequests.length === 0 ? (
                <div className="admin-empty">No service requests found.</div>
              ) : (
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Request ID</th>
                      <th>Service</th>
                      <th>User</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {serviceRequests.map(req => (
                      <tr key={req.id}>
                        <td className="req-id">{req.request_id}</td>
                        <td>{formatServiceName(req.service_type)}</td>
                        <td>
                          <div className="req-user-info">
                            <span>{req.user_name || "—"}</span>
                            <span className="req-user-email">{req.user_email}</span>
                          </div>
                        </td>
                        <td>
                          <span className={`status-badge ${req.status}`}>
                            {req.status === "pending" && <Clock size={11} />}
                            {req.status === "approved" && <CheckCircle size={11} />}
                            {req.status === "rejected" && <XCircle size={11} />}
                            {req.status}
                          </span>
                        </td>
                        <td>{formatDate(req.created_at)}</td>
                        <td>
                          <div className="admin-actions">
                            {req.status !== "approved" && (
                              <button
                                className="admin-action-btn approve"
                                onClick={() => updateStatus(req.id, "approved")}
                              >
                                <CheckCircle size={13} /> Approve
                              </button>
                            )}
                            {req.status !== "rejected" && (
                              <button
                                className="admin-action-btn reject"
                                onClick={() => updateStatus(req.id, "rejected")}
                              >
                                <XCircle size={13} /> Reject
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
