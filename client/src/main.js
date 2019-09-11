import 'bootstrap/dist/css/bootstrap.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false
Vue.use(BootstrapVue);
Vue.use(require('vue-moment'));

new Vue({
  render: h => h(App),
}).$mount('#app')
