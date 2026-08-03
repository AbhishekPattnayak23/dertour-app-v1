import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { PublicClientApplication, InteractionRequiredAuthError } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: process.env.REACT_APP_AZURE_CLIENT_ID || '',
    authority: process.env.REACT_APP_AZURE_AUTHORITY || 'https://login.microsoftonline.com/common',
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};

const loginRequest = {
  scopes: ['User.Read'],
};

const msalInstance = new PublicClientApplication(msalConfig);

export const AuthContext = createContext({
  isAuthenticated: false,
  user: null,
  login: () => {},
  logout: () => {},
  getAccessToken: () => Promise.resolve(''),
  isLoading: true,
});

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeMsal = async () => {
      try {
        await msalInstance.initialize();
        const accounts = msalInstance.getAllAccounts();
        
        if (accounts.length > 0) {
          msalInstance.setActiveAccount(accounts[0]);
          setUser(accounts[0]);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('MSAL initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeMsal();
  }, []);

  const login = useCallback(async () => {
    try {
      setIsLoading(true);
      const loginResponse = await msalInstance.loginPopup(loginRequest);
      
      if (loginResponse) {
        msalInstance.setActiveAccount(loginResponse.account);
        setUser(loginResponse.account);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      await msalInstance.logoutPopup();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getAccessToken = useCallback(async (scopes = ['User.Read']) => {
    try {
      const account = msalInstance.getActiveAccount();
      if (!account) {
        throw new Error('No active account found');
      }

      const silentRequest = {
        scopes,
        account,
      };

      const response = await msalInstance.acquireTokenSilent(silentRequest);
      return response.accessToken;
    } catch (error) {
      if (error instanceof InteractionRequiredAuthError) {
        try {
          const response = await msalInstance.acquireTokenPopup({
            scopes,
          });
          return response.accessToken;
        } catch (interactiveError) {
          console.error('Interactive token acquisition error:', interactiveError);
          throw interactiveError;
        }
      } else {
        console.error('Token acquisition error:', error);
        throw error;
      }
    }
  }, []);

  const value = {
    isAuthenticated,
    user,
    login,
    logout,
    getAccessToken,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};