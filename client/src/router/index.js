import Vue from 'vue';
import Router from 'vue-router';
import ControlPanel from '@/components/ControlPanel';
import CustomHeader from '@/components/CustomHeader';

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'ControlPanel',
      component: ControlPanel,
    },
    {
      path: '/header',
      name: 'CustomHeader',
      component: CustomHeader,
    },
  ],
});
