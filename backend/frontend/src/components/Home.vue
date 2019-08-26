<template>
  <div>
    <p>Reply from backend: {{ result }}</p>
    <button @click="getRandom">Get new result</button>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data () {
    return {
      randomNumber: 0
    }
  },
  methods: {
    getRandom () {
      this.result = this.getRandomFromBackend()
    },
    getRandomFromBackend () {
      const path = `http://0.0.0.0:8080/api/test1`
      axios.get(path)
      .then(response => {
        this.result = response.data.text
      })
      .catch(error => {
        console.log(error)
      })
    }
  },
  created () {
    this.getRandom()
  }
}
</script>
