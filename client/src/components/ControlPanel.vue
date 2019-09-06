<template>
  <div>
    <b-card no-body>
      <b-tabs pills card vertical>
        <b-tab title="Available Sites" active>
          <b-card-text>
            <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Site</th>
              <th scope="col">Production</th>
              <th scope="col">Staging</th>
              <th scope="col">Custodian</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in msg" :key="index">
              <td>{{ item.site_name }}</td>
              <td>{{ item.production_url }}</td>
              <td>{{ item.staging_url }}</td>
              <td> {{ item.custodian }} </td>
              <td>
                <button type="button" class="btn btn-success btn-sm">Create Editor</button>
              </td>
            </tr>
          </tbody>
        </table>
          </b-card-text>
        </b-tab>
        <b-tab title="Tab 2"><b-card-text>Tab Contents 2</b-card-text></b-tab>
        <b-tab title="Tab 3"><b-card-text>Tab Contents 3</b-card-text></b-tab>
      </b-tabs>
    </b-card>
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
