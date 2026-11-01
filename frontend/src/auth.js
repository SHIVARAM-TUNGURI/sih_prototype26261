/**
 * Demo-only officer authentication for the Pramaan prototype.
 *
 * NOTE: credentials are checked in the browser and the session lives in
 * sessionStorage, so this is NOT real security. It exists to demonstrate the
 * applicant / officer separation. A production system would use server-side
 * authentication (e.g. SSO / OTP) with role-based access control.
 */

const SESSION_KEY = 'pramaan_officer';

// Demo credentials (shown on the login page for the presentation)
export const DEMO_OFFICER_ID = 'officer';
export const DEMO_PASSWORD = 'pramaan123';

export function loginOfficer(officerId, password) {
  const ok =
    officerId.trim().toLowerCase() === DEMO_OFFICER_ID && password === DEMO_PASSWORD;
  if (ok) {
    try {
      sessionStorage.setItem(SESSION_KEY, officerId.trim());
    } catch {
      /* storage unavailable - login will not persist */
    }
  }
  return ok;
}

export function logoutOfficer() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export function isOfficerLoggedIn() {
  try {
    return Boolean(sessionStorage.getItem(SESSION_KEY));
  } catch {
    return false;
  }
}
