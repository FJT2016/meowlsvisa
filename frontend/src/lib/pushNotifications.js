const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}

export function pushSupported() {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return null;
  try {
    const registration = await navigator.serviceWorker.register('/sw.js');
    return registration;
  } catch (err) {
    console.error('SW registration failed', err);
    return null;
  }
}

export async function subscribeToPush() {
  if (!pushSupported()) return { ok: false, reason: 'unsupported' };

  // Ensure permission
  let permission = Notification.permission;
  if (permission === 'default') permission = await Notification.requestPermission();
  if (permission !== 'granted') return { ok: false, reason: 'denied' };

  const registration = await navigator.serviceWorker.ready;

  // Get VAPID public key from backend
  const keyResp = await fetch(`${BACKEND_URL}/api/push/vapid-public-key`, {
    credentials: 'include'
  });
  if (!keyResp.ok) return { ok: false, reason: 'no_vapid' };
  const { public_key } = await keyResp.json();

  // Subscribe (or get existing subscription)
  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(public_key)
    });
  }

  // Send to backend
  const resp = await fetch(`${BACKEND_URL}/api/push/subscribe`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription.toJSON())
  });
  if (!resp.ok) return { ok: false, reason: 'backend' };
  return { ok: true };
}

export async function unsubscribeFromPush() {
  if (!('serviceWorker' in navigator)) return { ok: false };
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();
  if (!subscription) return { ok: true };
  const endpointBody = subscription.toJSON();
  await subscription.unsubscribe();
  await fetch(`${BACKEND_URL}/api/push/unsubscribe`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(endpointBody)
  }).catch(() => {});
  return { ok: true };
}
