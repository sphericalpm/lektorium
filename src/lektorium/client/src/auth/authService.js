import auth0 from "auth0-js";
import { EventEmitter } from "events";

function authService() {
  const webAuth = new auth0.WebAuth({
    domain: $($.find('body')).data('auth0-domain'),
    redirectUri: `${window.location.origin}/callback`,
    clientID: $($.find('body')).data('auth0-id'),
    responseType: "id_token",
    scope: "openid profile email"
  });

  const localStorageKey = "loggedIn";
  const loginEvent = "loginEvent";

  class AuthService extends EventEmitter {
    idToken = null;
    profile = null;
    tokenExpiry = null;

    login(customState) {
      webAuth.authorize({
        appState: customState
      });
    }

    logOut() {
      localStorage.removeItem(localStorageKey);

      this.idToken = null;
      this.tokenExpiry = null;
      this.profile = null;

      webAuth.logout({
        returnTo: `${window.location.origin}`
      });

      this.emit(loginEvent, { loggedIn: false });
    }

    handleAuthentication() {
      return new Promise((resolve, reject) => {
        webAuth.parseHash((err, authResult) => {
          if (err) {
            this.emit(loginEvent, {
              loggedIn: false,
              error: err,
              errorMsg: err.statusText
            });
            reject(err);
          } else {
            this.localLogin(authResult);
            resolve(authResult.idToken);
          }
        });
      });
    }

    isAuthenticated() {
      return (
        Date.now() < this.tokenExpiry &&
        localStorage.getItem(localStorageKey) === "true"
      );
    }

    isIdTokenValid() {
      return this.idToken && this.tokenExpiry && Date.now() < this.tokenExpiry;
    }

    getIdToken() {
      return new Promise((resolve, reject) => {
        if (this.isIdTokenValid()) {
          resolve(this.idToken);
        } else if (this.isAuthenticated()) {
          this.renewTokens().then(authResult => {
            resolve(authResult.idToken);
          }, reject);
        } else {
          resolve();
        }
      });
    }

    localLogin(authResult) {
      this.idToken = authResult.idToken;
      this.profile = authResult.idTokenPayload;

      // Convert the expiry time from seconds to milliseconds,
      // required by the Date constructor
      this.tokenExpiry = new Date(this.profile.exp * 1000);

      localStorage.setItem(localStorageKey, "true");

      this.emit(loginEvent, {
        loggedIn: true,
        profile: authResult.idTokenPayload,
        state: authResult.appState || {}
      });
    }

    renewTokens() {
      return new Promise((resolve, reject) => {
        if (localStorage.getItem(localStorageKey) !== "true") {
          return reject("Not logged in");
        }

        webAuth.checkSession({}, (err, authResult) => {
          if (err) {
            reject(err);
          } else {
            this.localLogin(authResult);
            resolve(authResult);
          }
        });
      });
    }
  }

  const service = new AuthService();
  service.setMaxListeners(5);
  return service;
}

export default authService;
