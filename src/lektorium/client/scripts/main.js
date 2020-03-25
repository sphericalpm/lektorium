let router = new VueRouter({
    mode: 'history',
    routes: [{
        path: '/',
        component: httpVueLoader('/components/App.vue'),
        children: [
            {path: '', component: httpVueLoader('/components/ControlPanel.vue')},
            {path: 'profile', component: httpVueLoader('/components/Profile.vue')},
            {path: 'callback', component: httpVueLoader('/components/Callback.vue')},
        ],
    }],
});

router.beforeEach(((router, to, from, next) => {
    if (router.app.$auth === undefined || to.path === "/callback" || router.app.$auth.isAuthenticated()) {
        return next();
    }
    router.app.$auth.login({ target: to.fullPath });
}).bind(undefined, router));

if (_.get(lektoriumAuth0Config, 'domain')) {
    authServiceInstall(Vue);
};

new Vue({el: '#app', router});
