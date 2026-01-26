import React from 'react';
import { Link } from 'react-router-dom';
import { Plane, FileText, Clock, CheckCircle, Globe, Shield, Building, Briefcase, Heart } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Home = () => {
  const visaTypes = [
    {
      icon: <Plane className="h-8 w-8" />,
      title: 'Tourist Visa',
      description: 'For leisure travel and sightseeing. Valid for up to 90 days.',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      icon: <Briefcase className="h-8 w-8" />,
      title: 'Business Visa',
      description: 'For business meetings, conferences, and trade activities.',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      icon: <Heart className="h-8 w-8" />,
      title: 'Medical Visa',
      description: 'For medical treatment and accompanying attendants.',
      color: 'text-red-600',
      bgColor: 'bg-red-50'
    },
    {
      icon: <Building className="h-8 w-8" />,
      title: 'Conference Visa',
      description: 'For attending conferences, seminars, and workshops.',
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    }
  ];

  const steps = [
    { icon: <FileText />, title: 'Fill Application', description: 'Complete the online form' },
    { icon: <Globe />, title: 'Upload Documents', description: 'Submit required documents' },
    { icon: <Clock />, title: 'Track Status', description: 'Monitor your application' },
    { icon: <CheckCircle />, title: 'Receive e-Visa', description: 'Get approved and travel' }
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <section 
        className="relative h-[600px] flex items-center justify-center noise-texture"
        style={{
          backgroundImage: `linear-gradient(rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 0.7)), url('https://images.unsplash.com/photo-1750155680590-328cdc01709e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxOTJ8MHwxfHNlYXJjaHwxfHxtYWplc3RpYyUyMG1vdW50YWluJTIwbGFuZHNjYXBlJTIwbmF0dXJlfGVufDB8fHx8MTc2OTQzNDEzNnww&ixlib=rb-4.1.0&q=85')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
        data-testid="hero-section"
      >
        <div className="relative z-10 text-center max-w-4xl mx-auto px-6">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 tracking-tight">
            Welcome to Meowls e-Visa Portal
          </h1>
          <p className="text-lg md:text-xl text-slate-200 mb-8 leading-relaxed">
            Apply for your electronic visa online. Fast, secure, and hassle-free visa processing for the Republic of Meowls.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/register" 
              className="btn-primary px-8 py-4 text-lg inline-block"
              data-testid="apply-now-button"
            >
              Apply for e-Visa
            </Link>
            <Link 
              to="/track" 
              className="bg-white text-slate-900 hover:bg-slate-100 px-8 py-4 text-lg rounded-md font-medium transition-all inline-block"
              data-testid="track-application-button"
            >
              Track Application
            </Link>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Visa Types</h2>
            <p className="text-lg text-slate-600">Choose the visa category that suits your purpose of visit</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {visaTypes.map((visa, index) => (
              <div
                key={index}
                className="bg-white border border-slate-200 rounded-xl p-6 card-hover"
                data-testid={`visa-type-${index}`}
              >
                <div className={`${visa.bgColor} ${visa.color} w-16 h-16 rounded-lg flex items-center justify-center mb-4`}>
                  {visa.icon}
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">{visa.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{visa.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Application Process</h2>
            <p className="text-lg text-slate-600">Simple steps to get your e-Visa</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="relative" data-testid={`process-step-${index}`}>
                <div className="text-center">
                  <div className="bg-slate-900 text-white w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    {step.icon}
                  </div>
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-amber-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">{step.title}</h3>
                  <p className="text-sm text-slate-600">{step.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5 bg-slate-300"></div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <Shield className="h-16 w-16 text-amber-500 mx-auto mb-6" />
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Apply?</h2>
          <p className="text-lg text-slate-300 mb-8 leading-relaxed">
            Start your visa application today. The process takes only 10-15 minutes.
          </p>
          <Link 
            to="/register" 
            className="btn-primary px-8 py-4 text-lg inline-block"
            data-testid="footer-apply-button"
          >
            Start Application
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Home;