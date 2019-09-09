<template>
  <div id="app">
    <CustomHeader />
    <ControlPanel />
  </div>
</template>

<script>
import CustomHeader from '@/components/CustomHeader';
import ControlPanel from '@/components/ControlPanel';

export default {
  name: 'app',
  components: {
    CustomHeader,
    ControlPanel,
  }
}
</script>

<style>

</style>
