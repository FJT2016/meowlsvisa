import React from 'react';
import { Shield, Mail, MapPin } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-slate-900 text-white mt-20">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Shield className="h-6 w-6 text-amber-500" />
              <h3 className="text-lg font-bold">Meowls e-Visa</h3>
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              Official electronic visa application portal for the Republic of Meowls.
              Secure, fast, and reliable visa processing.
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-4 text-amber-500">Quick Links</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="/" className="text-slate-300 hover:text-white transition-colors">Home</a></li>
              <li><a href="/track" className="text-slate-300 hover:text-white transition-colors">Track Application</a></li>
              <li><a href="/login" className="text-slate-300 hover:text-white transition-colors">Login</a></li>
              <li><a href="/register" className="text-slate-300 hover:text-white transition-colors">Apply for Visa</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4 text-amber-500">Contact</h4>
            <div className="space-y-3 text-sm">
              <div className="flex items-start space-x-2">
                <Mail className="h-4 w-4 mt-0.5 text-amber-500" />
                <div>
                  <p className="text-slate-300">visa@meowls.gov</p>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <MapPin className="h-4 w-4 mt-0.5 text-amber-500" />
                <div>
                  <p className="text-slate-300">Ministry of Immigration</p>
                  <p className="text-slate-400 text-xs">Meowls City, Republic of Meowls</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-700 mt-8 pt-8 text-center">
          <p className="text-sm text-slate-400">
            © {new Date().getFullYear()} Republic of Meowls. All rights reserved. | Official Government Portal
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;