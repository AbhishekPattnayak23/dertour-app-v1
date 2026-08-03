import { PublicClientApplication } from '@azure/msal-browser';
import { apiClient } from './apiClient';

// MSAL configuration
const msalConfig = {
  auth: {
    clientId: process.env.REACT_APP_AZURE_CLIENT_ID || '',
    authority: process.env.REACT_APP_AZURE_AUTHORITY || 'https://login.microsoftonline.com/common',
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case 'Error':
            console.error(message);
            break;
          case 'Info':
            console.info(message);
            break;
          case 'Verbose':
            console.debug(message);
            break;
          case 'Warning':
            console.warn(message);
            break;
        }
      }
    }
  }
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: ['User.Read', 'openid', 'profile'],
  prompt: 'select_account'
};

const silentRequest = {
  scopes: ['User.Read'],
  account: null
};

class AuthService {
  constructor() {
    this.isInitialized = false;
    this.currentUser = null;
    this.accessToken = null;
  }

  async initialize() {
    if (this.isInitialized) return;
    
    try {
      await msalInstance.initialize();
      await msalInstance.handleRedirectPromise();
      this.isInitialized = true;
      
      const accounts = msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        this.currentUser = accounts[0];
        await this.acquireTokenSilently();
      }
    } catch (error) {
      console.error('Failed to initialize MSAL:', error);
      throw error;
    }
  }

  async login() {
    try {
      const loginResponse = await msalInstance.loginPopup(loginRequest);
      this.currentUser = loginResponse.account;
      this.accessToken = loginResponse.accessToken;
      
      this.setApiClientToken(this.accessToken);
      return loginResponse;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async loginRedirect() {
    try {
      await msalInstance.loginRedirect(loginRequest);
    } catch (error) {
      console.error('Login redirect failed:', error);
      throw error;
    }
  }

  async logout() {
    try {
      const logoutRequest = {
        account: this.currentUser,
        postLogoutRedirectUri: msalConfig.auth.postLogoutRedirectUri
      };
      
      this.currentUser = null;
      this.accessToken = null;
      this.removeApiClientToken();
      
      await msalInstance.logoutPopup(logoutRequest);
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }

  async logoutRedirect() {
    try {
      const logoutRequest = {
        account: this.currentUser,
        postLogoutRedirectUri: msalConfig.auth.postLogoutRedirectUri
      };
      
      this.currentUser = null;
      this.accessToken = null;
      this.removeApiClientToken();
      
      await msalInstance.logoutRedirect(logoutRequest);
    } catch (error) {
      console.error('Logout redirect failed:', error);
      throw error;
    }
  }

  async acquireTokenSilently() {
    if (!this.currentUser) {
      throw new Error('No user account available');
    }

    try {
      silentRequest.account = this.currentUser;
      const tokenResponse = await msalInstance.acquireTokenSilent(silentRequest);
      this.accessToken = tokenResponse.accessToken;
      
      this.setApiClientToken(this.accessToken);
      return tokenResponse;
    } catch (error) {
      console.warn('Silent token acquisition failed:', error);
      
      if (error.name === 'InteractionRequiredAuthError') {
        try {
          const tokenResponse = await msalInstance.acquireTokenPopup(loginRequest);
          this.accessToken = tokenResponse.accessToken;
          
          this.setApiClientToken(this.accessToken);
          return tokenResponse;
        } catch (interactiveError) {
          console.error('Interactive token acquisition failed:', interactiveError);
          throw interactiveError;
        }
      }
      throw error;
    }
  }

  async getAccessToken() {
    if (!this.accessToken) {
      await this.acquireTokenSilently();
    }
    return this.accessToken;
  }

  getCurrentUser() {
    return this.currentUser;
  }

  isAuthenticated() {
    return !!this.currentUser && !!this.accessToken;
  }

  getUserDisplayName() {
    return this.currentUser?.name || this.currentUser?.username || 'User';
  }

  getUserEmail() {
    return this.currentUser?.username || this.currentUser?.mail || '';
  }

  setApiClientToken(token) {
    if (apiClient) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  removeApiClientToken() {
    if (apiClient) {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  }

  onAuthStateChanged(callback) {
    const accounts = msalInstance.getAllAccounts();
    callback(accounts.length > 0 ? accounts[0] : null);
    
    return () => {};
  }

  async refreshToken() {
    try {
      await this.acquireTokenSilently();
      return this.accessToken;
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }

  getTokenClaims() {
    if (!this.currentUser) return null;
    
    return {
      oid: this.currentUser.localAccountId,
      name: this.currentUser.name,
      preferred_username: this.currentUser.username,
      tid: this.currentUser.tenantId
    };
  }
}

export const authService = new AuthService();

// Initialize the auth service when the module loads
authService.initialize().catch(error => {
  console.error('Auth service initialization failed:', error);
});