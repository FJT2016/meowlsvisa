import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, Upload } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ApplyVisa = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [applicationId, setApplicationId] = useState(null);
  const [formData, setFormData] = useState({
    visaType: 'tourist',
    fullName: '',
    dateOfBirth: '',
    nationality: '',
    passportNumber: '',
    passportExpiry: '',
    email: '',
    phone: '',
    address: '',
    purposeOfVisit: '',
    arrivalDate: '',
    departureDate: '',
    accommodationAddress: ''
  });
  const [documents, setDocuments] = useState({
    passport: null,
    photo: null
  });

  React.useEffect(() => {
    fetchUser();
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

  const steps = [
    { title: 'Visa Type', icon: '1' },
    { title: 'Personal Info', icon: '2' },
    { title: 'Travel Details', icon: '3' },
    { title: 'Documents', icon: '4' },
    { title: 'Review', icon: '5' }
  ];

  const handleNext = async () => {
    if (currentStep === 2 && !applicationId) {
      await saveApplication();
    }
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const saveApplication = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/applications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          visa_type: formData.visaType,
          personal_info: {
            full_name: formData.fullName,
            date_of_birth: formData.dateOfBirth,
            nationality: formData.nationality,
            passport_number: formData.passportNumber,
            passport_expiry: formData.passportExpiry,
            email: formData.email,
            phone: formData.phone,
            address: formData.address
          },
          travel_details: {
            purpose: formData.purposeOfVisit,
            arrival_date: formData.arrivalDate,
            departure_date: formData.departureDate,
            accommodation: formData.accommodationAddress
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setApplicationId(data.application_id);
        toast.success('Application saved as draft');
      }
    } catch (error) {
      console.error('Error saving application:', error);
      toast.error('Failed to save application');
    }
  };

  const handleDocumentUpload = async (docType, file) => {
    if (!applicationId) {
      toast.error('Please complete previous steps first');
      return;
    }

    const formDataObj = new FormData();
    formDataObj.append('file', file);

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/applications/${applicationId}/documents?doc_type=${docType}`,
        {
          method: 'POST',
          credentials: 'include',
          body: formDataObj
        }
      );

      if (response.ok) {
        setDocuments({ ...documents, [docType]: file.name });
        toast.success(`${docType} uploaded successfully`);
      }
    } catch (error) {
      console.error('Error uploading document:', error);
      toast.error('Failed to upload document');
    }
  };

  const handleSubmit = async () => {
    if (!applicationId) {
      toast.error('Application not created');
      return;
    }

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/applications/${applicationId}/submit`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );

      if (response.ok) {
        toast.success('Application submitted successfully!');
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Error submitting application:', error);
      toast.error('Failed to submit application');
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Select Visa Type</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {['tourist', 'business', 'medical', 'conference'].map((type) => (
                <label
                  key={type}
                  className={`border-2 rounded-xl p-6 cursor-pointer transition-all ${
                    formData.visaType === type
                      ? 'border-slate-900 bg-slate-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                  data-testid={`visa-type-${type}`}
                >
                  <input
                    type="radio"
                    name="visaType"
                    value={type}
                    checked={formData.visaType === type}
                    onChange={(e) => setFormData({ ...formData, visaType: e.target.value })}
                    className="sr-only"
                  />
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 capitalize">{type} Visa</h3>
                      <p className="text-sm text-slate-600 mt-1">
                        {type === 'tourist' && 'For leisure and sightseeing'}
                        {type === 'business' && 'For business activities'}
                        {type === 'medical' && 'For medical treatment'}
                        {type === 'conference' && 'For conferences and events'}
                      </p>
                    </div>
                    {formData.visaType === type && (
                      <Check className="h-6 w-6 text-slate-900" />
                    )}
                  </div>
                </label>
              ))}
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Personal Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="full-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Date of Birth</label>
                <input
                  type="date"
                  required
                  value={formData.dateOfBirth}
                  onChange={(e) => setFormData({ ...formData, dateOfBirth: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="dob-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Nationality</label>
                <input
                  type="text"
                  required
                  value={formData.nationality}
                  onChange={(e) => setFormData({ ...formData, nationality: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="nationality-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Passport Number</label>
                <input
                  type="text"
                  required
                  value={formData.passportNumber}
                  onChange={(e) => setFormData({ ...formData, passportNumber: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="passport-number-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Passport Expiry Date</label>
                <input
                  type="date"
                  required
                  value={formData.passportExpiry}
                  onChange={(e) => setFormData({ ...formData, passportExpiry: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="passport-expiry-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="email-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Phone Number</label>
                <input
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="phone-input"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">Address</label>
                <textarea
                  required
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="address-input"
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Travel Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">Purpose of Visit</label>
                <textarea
                  required
                  value={formData.purposeOfVisit}
                  onChange={(e) => setFormData({ ...formData, purposeOfVisit: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  placeholder="Briefly describe the purpose of your visit..."
                  data-testid="purpose-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Arrival Date</label>
                <input
                  type="date"
                  required
                  value={formData.arrivalDate}
                  onChange={(e) => setFormData({ ...formData, arrivalDate: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="arrival-date-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Departure Date</label>
                <input
                  type="date"
                  required
                  value={formData.departureDate}
                  onChange={(e) => setFormData({ ...formData, departureDate: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="departure-date-input"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">Accommodation Address in Meowls</label>
                <textarea
                  required
                  value={formData.accommodationAddress}
                  onChange={(e) => setFormData({ ...formData, accommodationAddress: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-slate-900"
                  data-testid="accommodation-input"
                />
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Upload Documents</h2>
            <div className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-8">
                <div className="text-center">
                  <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Passport Copy</h3>
                  <p className="text-sm text-slate-600 mb-4">Upload a clear copy of your passport (PDF or Image)</p>
                  <input
                    type="file"
                    accept="image/*,application/pdf"
                    onChange={(e) => handleDocumentUpload('passport', e.target.files[0])}
                    className="hidden"
                    id="passport-upload"
                    data-testid="passport-upload"
                  />
                  <label htmlFor="passport-upload" className="btn-primary cursor-pointer inline-block">
                    {documents.passport ? 'Change File' : 'Choose File'}
                  </label>
                  {documents.passport && (
                    <p className="text-sm text-green-600 mt-2">✓ {documents.passport}</p>
                  )}
                </div>
              </div>

              <div className="border-2 border-dashed border-slate-300 rounded-xl p-8">
                <div className="text-center">
                  <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Passport Photo</h3>
                  <p className="text-sm text-slate-600 mb-4">Upload a recent passport-size photograph</p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleDocumentUpload('photo', e.target.files[0])}
                    className="hidden"
                    id="photo-upload"
                    data-testid="photo-upload"
                  />
                  <label htmlFor="photo-upload" className="btn-primary cursor-pointer inline-block">
                    {documents.photo ? 'Change File' : 'Choose File'}
                  </label>
                  {documents.photo && (
                    <p className="text-sm text-green-600 mt-2">✓ {documents.photo}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Review & Submit</h2>
            <div className="bg-slate-50 rounded-xl p-6 space-y-6">
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Visa Type</h3>
                <p className="text-slate-700 capitalize">{formData.visaType}</p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Personal Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-slate-600">Name:</span> {formData.fullName}</div>
                  <div><span className="text-slate-600">Date of Birth:</span> {formData.dateOfBirth}</div>
                  <div><span className="text-slate-600">Nationality:</span> {formData.nationality}</div>
                  <div><span className="text-slate-600">Passport:</span> {formData.passportNumber}</div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Travel Details</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-slate-600">Arrival:</span> {formData.arrivalDate}</div>
                  <div><span className="text-slate-600">Departure:</span> {formData.departureDate}</div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Documents</h3>
                <div className="text-sm">
                  <div className="flex items-center space-x-2">
                    {documents.passport ? (
                      <><Check className="h-4 w-4 text-green-600" /> <span>Passport: {documents.passport}</span></>
                    ) : (
                      <span className="text-red-600">Passport: Not uploaded</span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 mt-2">
                    {documents.photo ? (
                      <><Check className="h-4 w-4 text-green-600" /> <span>Photo: {documents.photo}</span></>
                    ) : (
                      <span className="text-red-600">Photo: Not uploaded</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-sm text-amber-800">
                <strong>Note:</strong> Once submitted, you cannot edit your application. Please review all details carefully.
                Payment will be collected at immigration upon arrival.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar user={user} />

      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2" data-testid="apply-visa-title">Visa Application</h1>
          <p className="text-lg text-slate-600">Complete all steps to submit your application</p>
        </div>

        <div className="mb-12">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center" data-testid={`step-${index}`}>
                <div className="flex flex-col items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                      index <= currentStep
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-200 text-slate-600'
                    }`}
                  >
                    {index < currentStep ? <Check className="h-5 w-5" /> : step.icon}
                  </div>
                  <span className="text-xs mt-2 font-medium text-slate-600">{step.title}</span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`w-16 h-0.5 mx-2 transition-colors ${
                      index < currentStep ? 'bg-slate-900' : 'bg-slate-200'
                    }`}
                  ></div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-8 mb-6">
          {renderStepContent()}
        </div>

        <div className="flex justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className="btn-secondary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="back-button"
          >
            <ArrowLeft className="h-5 w-5" />
            <span>Back</span>
          </button>

          {currentStep === steps.length - 1 ? (
            <button
              onClick={handleSubmit}
              className="btn-primary flex items-center space-x-2"
              data-testid="submit-button"
            >
              <span>Submit Application</span>
              <Check className="h-5 w-5" />
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="btn-primary flex items-center space-x-2"
              data-testid="next-button"
            >
              <span>Next</span>
              <ArrowRight className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default ApplyVisa;