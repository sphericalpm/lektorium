import authService from "../auth/authService";

export default {
  install(Vue) {
    var service = authService();

    Vue.prototype.$auth = service;
    Vue.mixin({
      created() {
        if (this.handleLoginEvent) {
          service.addListener("loginEvent", this.handleLoginEvent);
        }
      },

      destroyed() {
        if (this.handleLoginEvent) {
          service.removeListener("loginEvent", this.handleLoginEvent);
        }
      }
    });
  }
};
