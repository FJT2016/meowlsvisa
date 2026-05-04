import React, { useEffect, useState } from 'react';
import { Download, X, Share } from 'lucide-react';

const DISMISSED_KEY = 'meowls_install_dismissed_at';
const DISMISS_DAYS = 7;

function isStandalone() {
  if (typeof window === 'undefined') return false;
  return (
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true // iOS
  );
}

function isIOS() {
  if (typeof navigator === 'undefined') return false;
  return /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
}

function dismissedRecently() {
  try {
    const ts = localStorage.getItem(DISMISSED_KEY);
    if (!ts) return false;
    const ageDays = (Date.now() - Number(ts)) / (1000 * 60 * 60 * 24);
    return ageDays < DISMISS_DAYS;
  } catch (_) {
    return false;
  }
}

const InstallAppBanner = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [visible, setVisible] = useState(false);
  const [iosMode, setIosMode] = useState(false);

  useEffect(() => {
    if (isStandalone() || dismissedRecently()) return;

    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setVisible(true);
    };
    window.addEventListener('beforeinstallprompt', handler);

    // iOS doesn't fire beforeinstallprompt — show manual instructions instead
    if (isIOS()) {
      setIosMode(true);
      setVisible(true);
    }

    const installedHandler = () => setVisible(false);
    window.addEventListener('appinstalled', installedHandler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      window.removeEventListener('appinstalled', installedHandler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const choice = await deferredPrompt.userChoice;
    setDeferredPrompt(null);
    if (choice.outcome === 'accepted') setVisible(false);
  };

  const handleDismiss = () => {
    try {
      localStorage.setItem(DISMISSED_KEY, String(Date.now()));
    } catch (_) {}
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      className="fixed bottom-4 inset-x-4 sm:inset-x-auto sm:right-4 sm:max-w-sm z-[60] bg-slate-900 text-white rounded-xl shadow-2xl border border-slate-700 p-4 flex items-start space-x-3"
      data-testid="install-app-banner"
      role="dialog"
      aria-label="Install Meowls e-Visa app"
    >
      <div className="bg-amber-600 w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0">
        <Download className="h-5 w-5 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm mb-1">Install Meowls e-Visa</p>
        {iosMode ? (
          <p className="text-xs text-slate-300 leading-relaxed flex items-center flex-wrap gap-1">
            Tap <Share className="inline h-3 w-3" /> then{' '}
            <span className="font-medium text-white">“Add to Home Screen”</span> to install this app and
            get push notifications.
          </p>
        ) : (
          <p className="text-xs text-slate-300 leading-relaxed">
            Install the app for faster access and instant push notifications when your visa is
            approved.
          </p>
        )}
        {!iosMode && deferredPrompt && (
          <button
            onClick={handleInstall}
            className="mt-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold px-3 py-1.5 rounded-md transition-colors"
            data-testid="install-app-button"
          >
            Install App
          </button>
        )}
      </div>
      <button
        onClick={handleDismiss}
        className="text-slate-400 hover:text-white transition-colors flex-shrink-0"
        aria-label="Dismiss install prompt"
        data-testid="install-app-dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

export default InstallAppBanner;
