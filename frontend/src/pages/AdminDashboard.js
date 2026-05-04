import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Users, Clock, CheckCircle, XCircle, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const AdminDashboard = () => {
  const [user, setUser] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    fetchUser();
    fetchApplications();
  }, []);

  // Reset to page 1 whenever filters change
  useEffect(() => {
    setPage(1);
  }, [searchTerm, statusFilter, pageSize]);

  const fetchUser = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
        credentials: 'include'
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/applications`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setApplications(data);
      }
    } catch (error) {
      console.error('Error fetching applications:', error);
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  const filteredApps = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    return applications.filter((app) => {
      if (statusFilter !== 'all' && app.status !== statusFilter) return false;
      if (!term) return true;
      return (
        app.application_id.toLowerCase().includes(term) ||
        app.personal_info?.full_name?.toLowerCase().includes(term) ||
        app.personal_info?.passport_number?.toLowerCase().includes(term) ||
        app.personal_info?.email?.toLowerCase().includes(term) ||
        app.personal_info?.nationality?.toLowerCase().includes(term)
      );
    });
  }, [applications, searchTerm, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredApps.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedApps = filteredApps.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );
  const showingFrom = filteredApps.length === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const showingTo = Math.min(currentPage * pageSize, filteredApps.length);

  const stats = [
    {
      title: 'Total Applications',
      value: applications.length,
      icon: <FileText className="h-6 w-6" />,
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600'
    },
    {
      title: 'Pending Review',
      value: applications.filter(a => ['submitted', 'under-review'].includes(a.status)).length,
      icon: <Clock className="h-6 w-6" />,
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-600'
    },
    {
      title: 'Approved',
      value: applications.filter(a => a.status === 'approved').length,
      icon: <CheckCircle className="h-6 w-6" />,
      bgColor: 'bg-green-50',
      textColor: 'text-green-600'
    },
    {
      title: 'Rejected',
      value: applications.filter(a => a.status === 'rejected').length,
      icon: <XCircle className="h-6 w-6" />,
      bgColor: 'bg-red-50',
      textColor: 'text-red-600'
    }
  ];

  const getStatusClass = (status) => {
    switch (status) {
      case 'approved': return 'status-badge status-approved';
      case 'rejected': return 'status-badge status-rejected';
      case 'under-review': return 'status-badge status-under-review';
      case 'submitted': return 'status-badge status-submitted';
      default: return 'status-badge status-draft';
    }
  };

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
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-xl border border-slate-200 p-6 card-hover"
              data-testid={`admin-stat-${index}`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.bgColor} ${stat.textColor} w-12 h-12 rounded-lg flex items-center justify-center`}>
                  {stat.icon}
                </div>
                <span className="text-3xl font-bold text-slate-900">{stat.value}</span>
              </div>
              <p className="text-sm font-medium text-slate-600">{stat.title}</p>
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
            <div>
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
            </div>
            <div>
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
                className="w-full md:w-36 px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                data-testid="page-size-select"
              >
                {PAGE_SIZE_OPTIONS.map((n) => (
                  <option key={n} value={n}>{n} / page</option>
                ))}
              </select>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto"></div>
            </div>
          ) : filteredApps.length === 0 ? (
            <div className="text-center py-12" data-testid="no-applications">
              <FileText className="h-16 w-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No applications found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Application ID
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Applicant
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Visa Type
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {pagedApps.map((app, index) => (
                    <tr key={app.application_id} className="hover:bg-slate-50 transition-colors" data-testid={`admin-app-row-${index}`}>
                      <td className="px-6 py-4">
                        <span className="text-sm font-mono text-slate-900">{app.application_id}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-slate-900">{app.personal_info.full_name}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-slate-900 capitalize">{app.visa_type}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={getStatusClass(app.status)}>{app.status}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-slate-600">
                          {new Date(app.created_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Link
                          to={`/admin/applications/${app.application_id}`}
                          className="text-sm font-medium text-slate-900 hover:text-slate-700"
                          data-testid={`review-app-${index}`}
                        >
                          Review →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && filteredApps.length > 0 && (
            <div
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-5 border-t border-slate-200 mt-5"
              data-testid="admin-pagination"
            >
              <p className="text-sm text-slate-600" data-testid="pagination-summary">
                Showing <span className="font-semibold text-slate-900">{showingFrom}</span>–
                <span className="font-semibold text-slate-900">{showingTo}</span> of{' '}
                <span className="font-semibold text-slate-900">{filteredApps.length}</span> applications
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