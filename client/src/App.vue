<template>
  <div id="app">
    <customheader></customheader>
    <router-view/>
  </div>
</template>

<script>
import CustomHeader from '@/components/CustomHeader';

export default {
  name: 'App',
  components: {
    customheader: CustomHeader,
  },
};
</script>

<style>

</style>
