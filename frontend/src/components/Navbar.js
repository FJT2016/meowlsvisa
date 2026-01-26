import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, LogOut, Home, LayoutDashboard, FileText } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Navbar = ({ user }) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <nav className="glass-effect border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2" data-testid="logo-link">
            <Shield className="h-8 w-8 text-slate-900" />
            <div>
              <h1 className="text-xl font-bold text-slate-900">Meowls e-Visa</h1>
              <p className="text-xs text-amber-600">Official Government Portal</p>
            </div>
          </Link>

          <div className="flex items-center space-x-6">
            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="flex items-center space-x-1 text-slate-600 hover:text-slate-900 transition-colors"
                  data-testid="dashboard-link"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  <span className="text-sm font-medium">Dashboard</span>
                </Link>
                
                {user.role === 'admin' && (
                  <Link
                    to="/admin"
                    className="flex items-center space-x-1 text-slate-600 hover:text-slate-900 transition-colors"
                    data-testid="admin-link"
                  >
                    <FileText className="h-4 w-4" />
                    <span className="text-sm font-medium">Admin</span>
                  </Link>
                )}

                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <p className="text-sm font-medium text-slate-900">{user.name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                  {user.picture && (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="h-10 w-10 rounded-full border-2 border-slate-200"
                    />
                  )}
                </div>

                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-red-600 hover:text-red-700 transition-colors"
                  data-testid="logout-button"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="text-sm font-medium">Logout</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/track"
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                  data-testid="track-link"
                >
                  Track Application
                </Link>
                <Link
                  to="/login"
                  className="btn-secondary text-sm"
                  data-testid="login-link"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="btn-primary text-sm"
                  data-testid="register-link"
                >
                  Apply Now
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;