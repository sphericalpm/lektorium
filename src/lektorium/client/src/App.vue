<template>
  <div id="app">
    <nav-bar />
    <div>
      <error />
      <div class="mt-5">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script>
import NavBar from './components/NavBar';

export default {
  name: 'app',
  components: {
    NavBar,
  },
  async created() {
    try {
      await this.$auth.renewTokens();
    } catch {
      // Supress the 'not logged in' error as we can illegitimately get that
      // when processing the callback url
    }
  }
}
</script>

<style>

</style>
