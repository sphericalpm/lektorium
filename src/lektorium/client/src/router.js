import Vue from "vue";
import Router from "vue-router";
import ControlPanel from './components/ControlPanel';
import Profile from "./views/Profile.vue";
import Callback from "./components/Callback.vue";
import auth from "./auth/authService";

Vue.use(Router);

const router = new Router({
  mode: "history",
  base: process.env.BASE_URL,
  routes: [
    {
      path: "/",
      name: "home",
      component: ControlPanel
    },
    {
      path: "/profile",
      name: "profile",
      component: Profile
    },
    {
      path: "/callback",
      name: "callback",
      component: Callback
    }
  ]
});

router.beforeEach(((router, to, from, next) => {
  if (router.app.$auth === undefined || to.path === "/callback" || router.app.$auth.isAuthenticated()) {
    return next();
  }
  router.app.$auth.login({ target: to.fullPath });
}).bind(undefined, router));

export default router;
