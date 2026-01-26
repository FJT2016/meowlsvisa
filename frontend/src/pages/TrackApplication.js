import React, { useState } from 'react';
import { Search, FileText } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TrackApplication = () => {
  const [applicationId, setApplicationId] = useState('');
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!applicationId.trim()) {
      toast.error('Please enter an application ID');
      return;
    }

    setLoading(true);
    setSearched(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/applications/${applicationId}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setApplication(data);
      } else {
        setApplication(null);
        toast.error('Application not found. Please check your ID and try again.');
      }
    } catch (error) {
      console.error('Error tracking application:', error);
      setApplication(null);
      toast.error('Failed to track application');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-50 border-green-200';
      case 'rejected': return 'text-red-600 bg-red-50 border-red-200';
      case 'under-review': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'submitted': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-4" data-testid="track-title">Track Your Application</h1>
          <p className="text-lg text-slate-600">Enter your application ID to check the status</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-8 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Application ID
              </label>
              <div className="relative">
                <FileText className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  value={applicationId}
                  onChange={(e) => setApplicationId(e.target.value)}
                  placeholder="e.g., app_a1b2c3d4e5f6"
                  className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                  data-testid="application-id-input"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 flex items-center justify-center space-x-2"
              data-testid="search-button"
            >
              <Search className="h-5 w-5" />
              <span>{loading ? 'Searching...' : 'Track Application'}</span>
            </button>
          </form>
        </div>

        {searched && application && (
          <div className="bg-white rounded-xl border border-slate-200 p-8" data-testid="application-result">
            <div className="text-center mb-8">
              <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full border-2 ${getStatusColor(application.status)} mb-4`}>
                <FileText className="h-10 w-10" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Application Status</h2>
              <p className={`text-lg font-semibold uppercase ${getStatusColor(application.status)} px-4 py-2 rounded-full inline-block`}>
                {application.status}
              </p>
            </div>

            <div className="space-y-6">
              <div className="border-t border-slate-200 pt-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <p className="text-sm text-slate-600 mb-1">Application ID</p>
                    <p className="font-mono font-semibold text-slate-900">{application.application_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 mb-1">Visa Type</p>
                    <p className="font-semibold text-slate-900 capitalize">{application.visa_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 mb-1">Applicant Name</p>
                    <p className="font-semibold text-slate-900">{application.personal_info.full_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600 mb-1">Submitted Date</p>
                    <p className="font-semibold text-slate-900">
                      {new Date(application.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>

              {application.status === 'approved' && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-green-800">
                    <strong>Congratulations!</strong> Your visa has been approved. You may proceed with your travel plans.
                    Payment will be collected at immigration upon arrival.
                  </p>
                </div>
              )}

              {application.status === 'rejected' && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-sm text-red-800">
                    <strong>Application Rejected:</strong> Unfortunately, your application has been rejected.
                    {application.admin_notes && ` Reason: ${application.admin_notes}`}
                  </p>
                </div>
              )}

              {['submitted', 'under-review'].includes(application.status) && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    <strong>Under Review:</strong> Your application is being processed. You will be notified once a decision is made.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {searched && !application && !loading && (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center" data-testid="not-found-result">
            <FileText className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Application Not Found</h3>
            <p className="text-slate-600">Please check your application ID and try again</p>
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
};

export default TrackApplication;