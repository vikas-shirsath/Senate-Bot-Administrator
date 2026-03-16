import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, AreaChart, Area,
} from "recharts";
import {
  BarChart3, Users, MessageSquare, FileText, Clock, TrendingUp,
  Globe, Activity, ArrowLeft, RefreshCw, AlertTriangle, CheckCircle2,
} from "lucide-react";
import "./AnalyticsDashboard.css";

const API_BASE = "http://localhost:8000";

const COLORS = ["#818cf8", "#34d399", "#f59e0b", "#f87171", "#60a5fa", "#a78bfa", "#fb923c", "#38bdf8"];

export default function AnalyticsDashboard({ getToken, onBack }) {
  const { t } = useTranslation();

  const [overview, setOverview] = useState(null);
  const [topQueries, setTopQueries] = useState([]);
  const [bottlenecks, setBottlenecks] = useState([]);
  const [completionRates, setCompletionRates] = useState([]);
  const [langStats, setLangStats] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  const authHeaders = useCallback(async () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${await getToken()}`,
  }), [getToken]);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const headers = await authHeaders();
      const [ov, tq, bn, cr, ls, tl] = await Promise.all([
        fetch(`${API_BASE}/analytics/overview`, { headers }).then(r => r.json()),
        fetch(`${API_BASE}/analytics/top-queries`, { headers }).then(r => r.json()),
        fetch(`${API_BASE}/analytics/bottlenecks`, { headers }).then(r => r.json()),
        fetch(`${API_BASE}/analytics/completion-rate`, { headers }).then(r => r.json()),
        fetch(`${API_BASE}/analytics/language-stats`, { headers }).then(r => r.json()),
        fetch(`${API_BASE}/analytics/usage-timeline`, { headers }).then(r => r.json()),
      ]);
      setOverview(ov);
      setTopQueries(tq);
      setBottlenecks(bn);
      setCompletionRates(cr);
      setLangStats(ls);
      setTimeline(tl);
      setLastRefresh(new Date());
    } catch (e) {
      console.error("Analytics fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, [authHeaders]);

  // Initial fetch + 30s polling
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const formatServiceName = (s) =>
    (s || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  if (loading && !overview) {
    return (
      <div className="analytics-loading">
        <Activity size={32} className="spin" />
        <p>Loading analytics…</p>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      {/* Header */}
      <div className="analytics-header">
        <div className="analytics-header-left">
          <button className="analytics-back-btn" onClick={onBack}>
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1>📊 Admin Analytics Dashboard</h1>
            <p className="analytics-subtitle">Real-time governance chatbot insights</p>
          </div>
        </div>
        <div className="analytics-header-right">
          {lastRefresh && (
            <span className="last-refresh">
              Updated {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button className="refresh-btn" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-icon users"><Users size={20} /></div>
          <div className="stat-info">
            <span className="stat-value">{overview?.total_users || 0}</span>
            <span className="stat-label">Total Users</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon chats"><MessageSquare size={20} /></div>
          <div className="stat-info">
            <span className="stat-value">{overview?.total_chats || 0}</span>
            <span className="stat-label">Total Chats</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon messages"><BarChart3 size={20} /></div>
          <div className="stat-info">
            <span className="stat-value">{overview?.total_messages || 0}</span>
            <span className="stat-label">Total Messages</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon requests"><FileText size={20} /></div>
          <div className="stat-info">
            <span className="stat-value">{overview?.total_service_requests || 0}</span>
            <span className="stat-label">Service Requests</span>
          </div>
        </div>
      </div>

      {/* Charts Row 1: Top Queries + Completion Rates */}
      <div className="charts-row">
        <div className="chart-card wide">
          <h3><TrendingUp size={16} /> Top User Queries</h3>
          {topQueries.length === 0 ? (
            <div className="chart-empty">No query data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={topQueries} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
                <YAxis dataKey="intent" type="category" width={140} stroke="var(--text-muted)" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "var(--bg-card)", border: "1px solid var(--border)",
                    borderRadius: "8px", fontSize: "12px",
                  }}
                />
                <Bar dataKey="count" fill="#818cf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="chart-card">
          <h3><CheckCircle2 size={16} /> Completion Rates</h3>
          {completionRates.length === 0 ? (
            <div className="chart-empty">No service data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={completionRates}
                  cx="50%" cy="50%"
                  innerRadius={55} outerRadius={90}
                  dataKey="completion_rate"
                  nameKey="service"
                  label={({ service, completion_rate }) =>
                    `${formatServiceName(service)} ${completion_rate}%`
                  }
                  labelLine={false}
                  fontSize={11}
                >
                  {completionRates.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val) => `${val}%`}
                  contentStyle={{
                    background: "var(--bg-card)", border: "1px solid var(--border)",
                    borderRadius: "8px", fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Charts Row 2: Timeline + Language */}
      <div className="charts-row">
        <div className="chart-card wide">
          <h3><Activity size={16} /> Usage Timeline (30 Days)</h3>
          {timeline.length === 0 ? (
            <div className="chart-empty">No usage data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={timeline} margin={{ left: 0, right: 10 }}>
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={10}
                  tickFormatter={d => d.slice(5)} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "var(--bg-card)", border: "1px solid var(--border)",
                    borderRadius: "8px", fontSize: "12px",
                  }}
                />
                <Area type="monotone" dataKey="messages" stroke="#818cf8" fill="url(#areaGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="chart-card">
          <h3><Globe size={16} /> Language Distribution</h3>
          {langStats.length === 0 ? (
            <div className="chart-empty">No language data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={langStats}
                  cx="50%" cy="50%"
                  outerRadius={80}
                  dataKey="count"
                  nameKey="language"
                  label={({ language, count }) => `${language} (${count})`}
                  fontSize={11}
                >
                  {langStats.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "var(--bg-card)", border: "1px solid var(--border)",
                    borderRadius: "8px", fontSize: "12px",
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Bottlenecks Table */}
      <div className="chart-card full-width">
        <h3><AlertTriangle size={16} /> Service Bottlenecks</h3>
        {bottlenecks.length === 0 ? (
          <div className="chart-empty">No bottleneck data yet</div>
        ) : (
          <div className="bottleneck-table-wrap">
            <table className="bottleneck-table">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Total</th>
                  <th>Pending</th>
                  <th>Approved</th>
                  <th>Rejected</th>
                  <th>Avg Processing</th>
                </tr>
              </thead>
              <tbody>
                {bottlenecks.map((b, i) => (
                  <tr key={i}>
                    <td className="service-name">{formatServiceName(b.service)}</td>
                    <td>{b.total}</td>
                    <td>
                      <span className={`status-pill pending ${b.pending > 5 ? "warn" : ""}`}>
                        {b.pending}
                      </span>
                    </td>
                    <td><span className="status-pill approved">{b.approved}</span></td>
                    <td><span className="status-pill rejected">{b.rejected}</span></td>
                    <td><Clock size={12} /> {b.avg_processing_time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
