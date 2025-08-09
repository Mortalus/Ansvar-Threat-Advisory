/**
 * Secure authentication cookie management
 * Implements secure cookie handling with 24-hour expiration
 */

const AUTH_COOKIE_NAME = 'auth_token';
const USER_COOKIE_NAME = 'user_data';
const COOKIE_MAX_AGE = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

interface CookieOptions {
  maxAge?: number;
  secure?: boolean;
  sameSite?: 'strict' | 'lax' | 'none';
  httpOnly?: boolean;
  path?: string;
}

/**
 * Set a secure cookie with proper security attributes
 */
export function setSecureCookie(
  name: string, 
  value: string, 
  options: CookieOptions = {}
): void {
  if (typeof document === 'undefined') return;

  const defaultOptions: CookieOptions = {
    maxAge: COOKIE_MAX_AGE,
    secure: window.location.protocol === 'https:',
    sameSite: 'lax',
    path: '/',
    ...options
  };

  let cookieString = `${name}=${encodeURIComponent(value)}`;
  
  if (defaultOptions.maxAge) {
    const expires = new Date(Date.now() + defaultOptions.maxAge).toUTCString();
    cookieString += `; expires=${expires}; max-age=${Math.floor(defaultOptions.maxAge / 1000)}`;
  }
  
  if (defaultOptions.path) {
    cookieString += `; path=${defaultOptions.path}`;
  }
  
  if (defaultOptions.secure) {
    cookieString += '; secure';
  }
  
  if (defaultOptions.sameSite) {
    cookieString += `; samesite=${defaultOptions.sameSite}`;
  }
  
  // Note: httpOnly cannot be set from client-side JavaScript
  // It would need to be set server-side for maximum security
  
  document.cookie = cookieString;
}

/**
 * Get a cookie value by name
 */
export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;

  const nameEQ = name + '=';
  const ca = document.cookie.split(';');
  
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) {
      return decodeURIComponent(c.substring(nameEQ.length, c.length));
    }
  }
  return null;
}

/**
 * Delete a cookie by setting it to expire immediately
 */
export function deleteCookie(name: string, path: string = '/'): void {
  if (typeof document === 'undefined') return;
  
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path};`;
}

/**
 * Set authentication token in secure cookie and localStorage
 */
export function setAuthToken(token: string): void {
  // Set in localStorage for immediate access
  if (typeof window !== 'undefined') {
    localStorage.setItem('session_token', token);
  }
  
  // Set in secure cookie for persistence
  setSecureCookie(AUTH_COOKIE_NAME, token, {
    maxAge: COOKIE_MAX_AGE,
    secure: typeof window !== 'undefined' && window.location.protocol === 'https:',
    sameSite: 'lax'
  });
}

/**
 * Set user data in secure cookie and localStorage
 */
export function setUserData(userData: any): void {
  const userDataString = JSON.stringify(userData);
  
  // Set in localStorage for immediate access
  if (typeof window !== 'undefined') {
    localStorage.setItem('user_data', userDataString);
  }
  
  // Set in secure cookie for persistence
  setSecureCookie(USER_COOKIE_NAME, userDataString, {
    maxAge: COOKIE_MAX_AGE,
    secure: typeof window !== 'undefined' && window.location.protocol === 'https:',
    sameSite: 'lax'
  });
}

/**
 * Get authentication token from localStorage or cookie fallback
 */
export function getAuthToken(): string | null {
  // First try localStorage for immediate access
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('session_token');
    if (token) return token;
  }
  
  // Fallback to cookie
  const cookieToken = getCookie(AUTH_COOKIE_NAME);
  if (cookieToken) {
    // Restore to localStorage for consistency
    if (typeof window !== 'undefined') {
      localStorage.setItem('session_token', cookieToken);
    }
    return cookieToken;
  }
  
  return null;
}

/**
 * Get user data from localStorage or cookie fallback
 */
export function getUserData(): any | null {
  // First try localStorage
  if (typeof window !== 'undefined') {
    const userData = localStorage.getItem('user_data');
    if (userData) {
      try {
        return JSON.parse(userData);
      } catch (e) {
        // Invalid JSON, remove it
        localStorage.removeItem('user_data');
      }
    }
  }
  
  // Fallback to cookie
  const cookieData = getCookie(USER_COOKIE_NAME);
  if (cookieData) {
    try {
      const parsedData = JSON.parse(cookieData);
      // Restore to localStorage for consistency
      if (typeof window !== 'undefined') {
        localStorage.setItem('user_data', cookieData);
      }
      return parsedData;
    } catch (e) {
      // Invalid JSON in cookie
      deleteCookie(USER_COOKIE_NAME);
    }
  }
  
  return null;
}

/**
 * Clear all authentication data
 */
export function clearAuth(): void {
  // Clear localStorage
  if (typeof window !== 'undefined') {
    localStorage.removeItem('session_token');
    localStorage.removeItem('user_data');
  }
  
  // Clear cookies
  deleteCookie(AUTH_COOKIE_NAME);
  deleteCookie(USER_COOKIE_NAME);
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

/**
 * Refresh authentication state from cookies
 * Useful for when the page loads and we need to restore auth state
 */
export function refreshAuthFromCookies(): boolean {
  const token = getAuthToken();
  const userData = getUserData();
  
  return token !== null && userData !== null;
}

/**
 * Logout user by clearing all authentication data
 */
export function logout(): void {
  clearAuth();
  
  // Redirect to login page
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}