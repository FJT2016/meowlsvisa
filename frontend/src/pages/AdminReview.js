import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, FileText, User, Calendar, MapPin, Mail, Phone, CheckCircle, XCircle, Clock } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminReview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    fetchUser();
    fetchApplication();
  }, [id]);

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

  const fetchApplication = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/applications/${id}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setApplication(data);
        setSelectedStatus(data.status);
        setNotes(data.admin_notes || '');
      } else {
        toast.error('Application not found');
      }
    } catch (error) {
      console.error('Error fetching application:', error);
      toast.error('Failed to load application');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedStatus) {
      toast.error('Please select a status');
      return;
    }

    setUpdating(true);

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/admin/applications/${id}/status`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            status: selectedStatus,
            notes: notes
          })
        }
      );

      if (response.ok) {
        const result = await response.json();
        if (result.email_sent) {
          if (selectedStatus === 'approved') {
            toast.success('Application approved! ✅ Email with visa document sent to applicant.');
          } else if (selectedStatus === 'rejected') {
            toast.success('Application rejected. 📧 Notification email sent to applicant.');
          }
        } else {
          toast.success('Application status updated successfully');
        }
        setTimeout(() => navigate('/admin'), 1500);
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update status');
      }
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error(error.message || 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar user={user} />
        <div className="max-w-7xl mx-auto px-6 py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto"></div>
        </div>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar user={user} />
        <div className="max-w-7xl mx-auto px-6 py-12 text-center">
          <FileText className="h-16 w-16 text-slate-300 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Application Not Found</h2>
          <Link to="/admin" className="btn-primary inline-block mt-4">
            Back to Admin Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar user={user} />

      <div className="max-w-7xl mx-auto px-6 py-12">
        <Link 
          to="/admin" 
          className="flex items-center space-x-2 text-slate-600 hover:text-slate-900 mb-6 transition-colors"
          data-testid="back-to-admin"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Admin Dashboard</span>
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-8">
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-slate-900 mb-2" data-testid="review-title">
                  Application Review
                </h1>
                <p className="text-slate-600 font-mono">{application.application_id}</p>
              </div>

              <div className="space-y-8">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>Visa Information</span>
                  </h2>
                  <div className="grid grid-cols-2 gap-4 bg-slate-50 rounded-lg p-4">
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Visa Type</p>
                      <p className="font-semibold text-slate-900 capitalize">{application.visa_type}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Application Date</p>
                      <p className="font-semibold text-slate-900">
                        {new Date(application.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center space-x-2">
                    <User className="h-5 w-5" />
                    <span>Personal Information</span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 rounded-lg p-4">
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Full Name</p>
                      <p className="font-medium text-slate-900">{application.personal_info.full_name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Date of Birth</p>
                      <p className="font-medium text-slate-900">{application.personal_info.date_of_birth}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Nationality</p>
                      <p className="font-medium text-slate-900">{application.personal_info.nationality}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Passport Number</p>
                      <p className="font-medium text-slate-900">{application.personal_info.passport_number}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Passport Expiry</p>
                      <p className="font-medium text-slate-900">{application.personal_info.passport_expiry}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1 flex items-center space-x-1">
                        <Mail className="h-3 w-3" />
                        <span>Email</span>
                      </p>
                      <p className="font-medium text-slate-900">{application.personal_info.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1 flex items-center space-x-1">
                        <Phone className="h-3 w-3" />
                        <span>Phone</span>
                      </p>
                      <p className="font-medium text-slate-900">{application.personal_info.phone}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm text-slate-600 mb-1 flex items-center space-x-1">
                        <MapPin className="h-3 w-3" />
                        <span>Address</span>
                      </p>
                      <p className="font-medium text-slate-900">{application.personal_info.address}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center space-x-2">
                    <Calendar className="h-5 w-5" />
                    <span>Travel Details</span>
                  </h2>
                  <div className="bg-slate-50 rounded-lg p-4 space-y-4">
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Purpose of Visit</p>
                      <p className="font-medium text-slate-900">{application.travel_details.purpose}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-600 mb-1">Arrival Date</p>
                        <p className="font-medium text-slate-900">{application.travel_details.arrival_date}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600 mb-1">Departure Date</p>
                        <p className="font-medium text-slate-900">{application.travel_details.departure_date}</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Accommodation in Meowls</p>
                      <p className="font-medium text-slate-900">{application.travel_details.accommodation}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-slate-200 p-6 sticky top-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-6">Update Status</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Current Status
                  </label>
                  <div className="bg-slate-50 rounded-lg p-3">
                    <span className="text-sm font-semibold text-slate-900 uppercase">{application.status}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    New Status
                  </label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                    data-testid="status-select"
                  >
                    <option value="submitted">Submitted</option>
                    <option value="under-review">Under Review</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Admin Notes
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={4}
                    placeholder="Add notes about this application..."
                    className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                    data-testid="notes-input"
                  />
                </div>

                <button
                  onClick={handleUpdateStatus}
                  disabled={updating || selectedStatus === application.status}
                  className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                  data-testid="update-status-button"
                >
                  {updating ? 'Updating...' : 'Update Status'}
                </button>

                <div className="pt-4 border-t border-slate-200 space-y-2">
                  <button
                    onClick={() => {
                      setSelectedStatus('approved');
                      setNotes('Application approved. All documents verified.');
                    }}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition-colors"
                    data-testid="quick-approve"
                  >
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Quick Approve</span>
                  </button>

                  <button
                    onClick={() => {
                      setSelectedStatus('rejected');
                      setNotes('Application rejected. Please provide valid documents.');
                    }}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-50 text-red-700 rounded-md hover:bg-red-100 transition-colors"
                    data-testid="quick-reject"
                  >
                    <XCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Quick Reject</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default AdminReview;