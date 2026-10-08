import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';

import axios from 'axios';


const API = `${process.env.REACT_APP_BACKEND_URL}/api`;


const AuthContext = createContext(null);


export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);


  /*
   * Check whether this browser already has
   * a valid authenticated session.
   *
   * Authentication is determined from the real
   * backend cookies:
   *
   * - access_token
   * - refresh_token
   * - session_token
   */
  const checkAuth = useCallback(async () => {

    /*
     * OAuth callback must be allowed to finish first.
     * AuthCallback will establish the Google session.
     */
    const hasOAuth =
      window.location.hash?.includes('session_id=') ||
      window.location.search?.includes('session_id=');

    if (hasOAuth) {
      setLoading(false);
      return;
    }


    /*
     * STEP 1:
     * Try normal /auth/me.
     */
    try {
      const response = await axios.get(
        `${API}/auth/me`,
        {
          withCredentials: true,
        }
      );

      setUser(response.data);
      setLoading(false);

      return;

    } catch (error) {
      /*
       * Do not immediately assume the user is signed out.
       *
       * A normal account has:
       *
       * access token = 1 hour
       * refresh token = 7 days
       *
       * So the access token can expire while the user
       * is still legitimately logged in.
       */
    }


    /*
     * STEP 2:
     * Try to refresh the access token.
     *
     * This is what lets a returning user stay logged in
     * instead of randomly getting sent to the landing page
     * after the 1-hour access token expires.
     */
    try {
      await axios.post(
        `${API}/auth/refresh`,
        {},
        {
          withCredentials: true,
        }
      );

      /*
       * STEP 3:
       * Now that the access token has been refreshed,
       * ask /auth/me again.
       */
      const response = await axios.get(
        `${API}/auth/me`,
        {
          withCredentials: true,
        }
      );

      setUser(response.data);
      setLoading(false);

      return;

    } catch (refreshError) {
      /*
       * STEP 4:
       *
       * Refresh failed too.
       *
       * There is no valid normal JWT session.
       *
       * BUT Google users may authenticate through
       * session_token rather than access_token.
       *
       * So give /auth/me one final chance.
       */
      try {
        const response = await axios.get(
          `${API}/auth/me`,
          {
            withCredentials: true,
          }
        );

        setUser(response.data);

      } catch (finalError) {
        /*
         * No valid session at all.
         *
         * This means the browser is effectively signed out.
         * RootGate will then show LandingPage.
         */
        setUser(null);
      }

      setLoading(false);
    }

  }, []);


  /*
   * Run authentication check when the app starts.
   *
   * This is the key to:
   *
   * Close browser
   *       ↓
   * Open website later
   *       ↓
   * Browser sends auth cookie
   *       ↓
   * /auth/me returns user
   *       ↓
   * Dashboard
   */
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);


  /*
   * Called after login, signup, Google authentication,
   * school selection, onboarding refreshes, etc.
   */
  const login = (userData) => {
    setUser(userData);
  };


  /*
   * Completely sign the user out.
   *
   * Once this finishes:
   *
   * user = null
   *
   * RootGate immediately renders LandingPage.
   */
  const logout = async () => {

    try {
      /*
       * Normal JWT logout.
       */
      await axios.post(
        `${API}/auth/logout`,
        {},
        {
          withCredentials: true,
        }
      );

    } catch (error) {
      console.warn(
        'Normal logout error:',
        error
      );
    }


    try {
      /*
       * Google logout.
       */
      await axios.post(
        `${API}/google-auth/logout`,
        {},
        {
          withCredentials: true,
        }
      );

    } catch (error) {
      console.warn(
        'Google logout error:',
        error
      );
    }


    /*
     * Clear frontend authentication state.
     */
    setUser(null);
  };


  return (
    <AuthContext.Provider
      value={{
        user,
        loading,

        login,
        logout,

        setUser,

        checkAuth,

        /*
         * Existing code uses refresh().
         */
        refresh: checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}


export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      'useAuth must be used within AuthProvider'
    );
  }

  return context;
};


export default AuthContext;
