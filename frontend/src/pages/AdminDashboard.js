import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Clock, CheckCircle, XCircle, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const AdminDashboard = () => {
  const [user, setUser] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [stats, setStats] = useState({ total: 0, pending: 0, approved: 0, rejected: 0 });

  const fetchUser = useCallback(async () => {
    try {
      const r = await fetch(`${BACKEND_URL}/api/auth/me`, { credentials: 'include' });
      if (r.ok) setUser(await r.json());
    } catch (e) { console.error(e); }
  }, []);

  // Stats: lightweight 1-per-status count calls (page_size=1 → we just want `total`)
  const fetchStats = useCallback(async () => {
    try {
      const [all, pending1, pending2, approved, rejected] = await Promise.all([
        fetch(`${BACKEND_URL}/api/admin/applications?page=1&page_size=1`, { credentials: 'include' }),
        fetch(`${BACKEND_URL}/api/admin/applications?page=1&page_size=1&status=submitted`, { credentials: 'include' }),
        fetch(`${BACKEND_URL}/api/admin/applications?page=1&page_size=1&status=under-review`, { credentials: 'include' }),
        fetch(`${BACKEND_URL}/api/admin/applications?page=1&page_size=1&status=approved`, { credentials: 'include' }),
        fetch(`${BACKEND_URL}/api/admin/applications?page=1&page_size=1&status=rejected`, { credentials: 'include' }),
      ]);
      const j = async (r) => (r.ok ? (await r.json()).total : 0);
      setStats({
        total: await j(all),
        pending: (await j(pending1)) + (await j(pending2)),
        approved: await j(approved),
        rejected: await j(rejected),
      });
    } catch (e) { console.error(e); }
  }, []);

  const fetchPage = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (statusFilter !== 'all') qs.set('status', statusFilter);
      if (searchTerm.trim()) qs.set('search', searchTerm.trim());

      const r = await fetch(`${BACKEND_URL}/api/admin/applications?${qs}`, {
        credentials: 'include',
      });
      if (!r.ok) throw new Error('failed');
      const data = await r.json();
      setItems(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (e) {
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter, searchTerm]);

  useEffect(() => {
    fetchUser();
    fetchStats();
  }, [fetchUser, fetchStats]);

  useEffect(() => { setPage(1); }, [searchTerm, statusFilter, pageSize]);

  // Debounce search by 300ms
  useEffect(() => {
    const t = setTimeout(fetchPage, searchTerm ? 300 : 0);
    return () => clearTimeout(t);
  }, [fetchPage, searchTerm]);

  const getStatusClass = (status) => {
    switch (status) {
      case 'approved': return 'status-badge status-approved';
      case 'rejected': return 'status-badge status-rejected';
      case 'under-review': return 'status-badge status-under-review';
      case 'submitted': return 'status-badge status-submitted';
      default: return 'status-badge status-draft';
    }
  };

  const statCards = [
    { title: 'Total Applications', value: stats.total, icon: <FileText className="h-6 w-6" />, bg: 'bg-blue-50', text: 'text-blue-600' },
    { title: 'Pending Review', value: stats.pending, icon: <Clock className="h-6 w-6" />, bg: 'bg-yellow-50', text: 'text-yellow-600' },
    { title: 'Approved', value: stats.approved, icon: <CheckCircle className="h-6 w-6" />, bg: 'bg-green-50', text: 'text-green-600' },
    { title: 'Rejected', value: stats.rejected, icon: <XCircle className="h-6 w-6" />, bg: 'bg-red-50', text: 'text-red-600' },
  ];

  const currentPage = Math.min(page, totalPages || 1);
  const showingFrom = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const showingTo = Math.min(currentPage * pageSize, total);

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar user={user} />

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2" data-testid="admin-dashboard-title">
            Admin Dashboard
          </h1>
          <p className="text-lg text-slate-600">Review and manage visa applications</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          {statCards.map((s, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-6 card-hover" data-testid={`admin-stat-${i}`}>
              <div className="flex items-center justify-between mb-4">
                <div className={`${s.bg} ${s.text} w-12 h-12 rounded-lg flex items-center justify-center`}>
                  {s.icon}
                </div>
                <span className="text-3xl font-bold text-slate-900">{s.value}</span>
              </div>
              <p className="text-sm font-medium text-slate-600">{s.title}</p>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by ID, name, passport, email, nationality..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                  data-testid="search-input"
                />
              </div>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full md:w-48 px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900 focus:border-transparent"
              data-testid="status-filter"
            >
              <option value="all">All Status</option>
              <option value="draft">Draft</option>
              <option value="submitted">Submitted</option>
              <option value="under-review">Under Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
            <select
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
              className="w-full md:w-36 px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900 focus:border-transparent"
              data-testid="page-size-select"
            >
              {PAGE_SIZE_OPTIONS.map((n) => <option key={n} value={n}>{n} / page</option>)}
            </select>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto"></div>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-12" data-testid="no-applications">
              <FileText className="h-16 w-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No applications found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Application ID</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Applicant</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Visa Type</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {items.map((app, index) => (
                    <tr key={app.application_id} className="hover:bg-slate-50 transition-colors" data-testid={`admin-app-row-${index}`}>
                      <td className="px-6 py-4"><span className="text-sm font-mono text-slate-900">{app.application_id}</span></td>
                      <td className="px-6 py-4"><span className="text-sm text-slate-900">{app.personal_info?.full_name}</span></td>
                      <td className="px-6 py-4"><span className="text-sm text-slate-900 capitalize">{app.visa_type}</span></td>
                      <td className="px-6 py-4"><span className={getStatusClass(app.status)}>{app.status}</span></td>
                      <td className="px-6 py-4"><span className="text-sm text-slate-600">{new Date(app.created_at).toLocaleDateString()}</span></td>
                      <td className="px-6 py-4">
                        <Link to={`/admin/applications/${app.application_id}`} className="text-sm font-medium text-slate-900 hover:text-slate-700" data-testid={`review-app-${index}`}>
                          Review →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && total > 0 && (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-5 border-t border-slate-200 mt-5" data-testid="admin-pagination">
              <p className="text-sm text-slate-600" data-testid="pagination-summary">
                Showing <span className="font-semibold text-slate-900">{showingFrom}</span>–
                <span className="font-semibold text-slate-900">{showingTo}</span> of{' '}
                <span className="font-semibold text-slate-900">{total}</span> applications
              </p>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="flex items-center space-x-1 px-3 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  data-testid="pagination-prev"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span>Prev</span>
                </button>
                <span className="px-3 py-2 text-sm text-slate-600" data-testid="pagination-page-info">
                  Page <span className="font-semibold text-slate-900">{currentPage}</span> of{' '}
                  <span className="font-semibold text-slate-900">{totalPages}</span>
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="flex items-center space-x-1 px-3 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  data-testid="pagination-next"
                >
                  <span>Next</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default AdminDashboard;
