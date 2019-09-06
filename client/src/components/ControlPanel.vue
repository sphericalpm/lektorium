<template>
  <div>
      <p>{{ msg }}</p>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ControlPanel',
  data() {
    return {
      msg: '',
    };
  },
  methods: {
    getAvailableSites() {
      const path = 'http://localhost:5000/sites';
      axios.get(path)
        .then((res) => {
          this.msg = res.data;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
  },
  created() {
    this.getAvailableSites();
  },
};
</script>

<style>

</style>
