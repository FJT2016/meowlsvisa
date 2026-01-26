import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, FileText, Calendar, User, MapPin, Mail, Phone, CheckCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ApplicationDetails = () => {
  const { id } = useParams();
  const [user, setUser] = useState(null);
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);

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

  const getStatusClass = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected': return 'bg-red-100 text-red-800 border-red-200';
      case 'under-review': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'submitted': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar user={user} />
        <div className="max-w-4xl mx-auto px-6 py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto"></div>
        </div>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar user={user} />
        <div className="max-w-4xl mx-auto px-6 py-12 text-center">
          <FileText className="h-16 w-16 text-slate-300 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Application Not Found</h2>
          <Link to="/dashboard" className="btn-primary inline-block mt-4">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar user={user} />

      <div className="max-w-4xl mx-auto px-6 py-12">
        <Link 
          to="/dashboard" 
          className="flex items-center space-x-2 text-slate-600 hover:text-slate-900 mb-6 transition-colors"
          data-testid="back-to-dashboard"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Link>

        <div className="bg-white rounded-xl border border-slate-200 p-8 mb-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2" data-testid="application-title">
                Application Details
              </h1>
              <p className="text-slate-600 font-mono">{application.application_id}</p>
            </div>
            <span
              className={`px-4 py-2 rounded-full text-sm font-semibold border ${getStatusClass(application.status)}`}
              data-testid="application-status"
            >
              {application.status.toUpperCase()}
            </span>
          </div>

          {application.status === 'approved' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6" data-testid="approval-notice">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <p className="text-sm text-green-800">
                  <strong>Congratulations!</strong> Your visa has been approved. Please proceed to immigration with this approval.
                </p>
              </div>
            </div>
          )}

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

            {application.admin_notes && (
              <div>
                <h2 className="text-xl font-semibold text-slate-900 mb-4">Admin Notes</h2>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <p className="text-slate-800">{application.admin_notes}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default ApplicationDetails;