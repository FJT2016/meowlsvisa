import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FileText, Plus, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser();
    fetchApplications();
  }, []);

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
      const response = await fetch(`${BACKEND_URL}/api/applications`, {
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'under-review':
        return <Clock className="h-5 w-5 text-blue-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'approved': return 'status-badge status-approved';
      case 'rejected': return 'status-badge status-rejected';
      case 'under-review': return 'status-badge status-under-review';
      case 'submitted': return 'status-badge status-submitted';
      default: return 'status-badge status-draft';
    }
  };

  const stats = [
    {
      title: 'Total Applications',
      value: applications.length,
      icon: <FileText className="h-6 w-6" />,
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600'
    },
    {
      title: 'Approved',
      value: applications.filter(a => a.status === 'approved').length,
      icon: <CheckCircle className="h-6 w-6" />,
      bgColor: 'bg-green-50',
      textColor: 'text-green-600'
    },
    {
      title: 'Pending',
      value: applications.filter(a => ['submitted', 'under-review'].includes(a.status)).length,
      icon: <Clock className="h-6 w-6" />,
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-600'
    },
    {
      title: 'Draft',
      value: applications.filter(a => a.status === 'draft').length,
      icon: <AlertCircle className="h-6 w-6" />,
      bgColor: 'bg-slate-50',
      textColor: 'text-slate-600'
    }
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar user={user} />

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2" data-testid="dashboard-title">
            Welcome back, {user?.name}!
          </h1>
          <p className="text-lg text-slate-600">Manage your visa applications</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-xl border border-slate-200 p-6 card-hover"
              data-testid={`stat-card-${index}`}
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

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900">Your Applications</h2>
          <Link
            to="/apply"
            className="btn-primary flex items-center space-x-2"
            data-testid="new-application-button"
          >
            <Plus className="h-5 w-5" />
            <span>New Application</span>
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto"></div>
          </div>
        ) : applications.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center" data-testid="no-applications">
            <FileText className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">No Applications Yet</h3>
            <p className="text-slate-600 mb-6">Start your first visa application today</p>
            <Link to="/apply" className="btn-primary inline-block">
              Apply for Visa
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Application ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Visa Type
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Submitted
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {applications.map((app, index) => (
                  <tr key={app.application_id} className="hover:bg-slate-50 transition-colors" data-testid={`application-row-${index}`}>
                    <td className="px-6 py-4">
                      <span className="text-sm font-mono text-slate-900">{app.application_id}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-900 capitalize">{app.visa_type}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(app.status)}
                        <span className={getStatusClass(app.status)}>{app.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-600">
                        {new Date(app.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        to={`/applications/${app.application_id}`}
                        className="text-sm font-medium text-slate-900 hover:text-slate-700"
                        data-testid={`view-application-${index}`}
                      >
                        View Details →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
};

export default Dashboard;