import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue'
import App from './App.vue'
import router from './router'
import AuthPlugin from './plugins/auth'
import HighlightJs from "./directives/highlight"
import VueMoment from 'vue-moment'
import moment from 'moment-timezone'

Vue.config.productionTip = false
Vue.use(BootstrapVue);
Vue.use(require('vue-shortkey'));
Vue.use(VueMoment, {
  moment,
});
if ($($.find('body')).data('auth0-domain')) {
	Vue.use(AuthPlugin);
	Vue.directive("highlightjs", HighlightJs);
}

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
