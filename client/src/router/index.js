import Vue from 'vue'
import Router from 'vue-router'
import ControlPanel from '@/components/ControlPanel'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'ControlPanel',
      component: ControlPanel
    }
  ]
})
