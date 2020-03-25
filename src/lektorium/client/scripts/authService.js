function parseJwt(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
};

function authService() {
    const webAuth = new auth0.WebAuth({
        domain: _.get(lektoriumAuth0Config, 'domain'),
        redirectUri: `${window.location.origin}/callback`,
        clientID: _.get(lektoriumAuth0Config, 'id'),
        audience: _.get(lektoriumAuth0Config, 'api'),
        responseType: 'id_token token',
        scope: 'openid profile email'
    });

    const localStorageKey = 'loggedIn';
    const loginEvent = 'loginEvent';

    class AuthService extends EventEmitter3 {
        idToken = null;
        accessToken = null;
        profile = null;
        tokenExpiry = null;

        login(customState) {
            webAuth.authorize({
                appState: customState
            });
        };

        logOut() {
            localStorage.removeItem(localStorageKey);

            this.idToken = null;
            this.accessToken = null;
            this.tokenExpiry = null;
            this.profile = null;

            webAuth.logout({
                returnTo: `${window.location.origin}`
            });

            this.emit(loginEvent, { loggedIn: false });
        };

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
        };

        isAuthenticated() {
            return (
                Date.now() < this.tokenExpiry &&
                localStorage.getItem(localStorageKey) === 'true'
            );
        };

        isTokenValid() {
            return this.idToken && this.tokenExpiry && Date.now() < this.tokenExpiry;
        };

        getTokens() {
            return new Promise((resolve, reject) => {
                if (this.isTokenValid()) {
                    resolve([this.idToken, this.accessToken]);
                } else if (this.isAuthenticated()) {
                    this.renewTokens().then(authResult => {
                        resolve([authResult.idToken, authResult.accessToken]);
                    }, reject);
                } else {
                    resolve();
                }
            });
        };

        localLogin(authResult) {
            var profile = JSON.parse(JSON.stringify(authResult.idTokenPayload));
            profile.access_token = parseJwt(authResult.accessToken);
            this.idToken = authResult.idToken;
            this.accessToken = authResult.accessToken;
            this.profile = profile;

            // Convert the expiry time from seconds to milliseconds,
            // required by the Date constructor
            this.tokenExpiry = new Date(this.profile.exp * 1000);

            localStorage.setItem(localStorageKey, 'true');

            this.emit(loginEvent, {
                loggedIn: true,
                profile: profile,
                state: authResult.appState || {}
            });
        };

        renewTokens() {
            return new Promise((resolve, reject) => {
                if (localStorage.getItem(localStorageKey) !== 'true') {
                    return reject('Not logged in');
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
    };

    const service = new AuthService();
    return service;
};

function authServiceInstall(Vue) {
    var service = authService();
    Vue.prototype.$auth = service;
    Vue.mixin({
        created() {
            if (this.handleLoginEvent) {
                service.addListener('loginEvent', this.handleLoginEvent);
            };
        },

        destroyed() {
            if (this.handleLoginEvent) {
                service.removeListener('loginEvent', this.handleLoginEvent);
            };
        },
    });
};
