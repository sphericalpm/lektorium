<template>
  <div>
    <b-card no-body>
      <b-tabs pills card vertical>
        <b-tab active>
          <template slot="title">
            Available Sites <b-badge pill> {{available_sites.length}} </b-badge>
          </template>
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
            <tr v-for="(site, index) in available_sites" :key="index">
              <td>{{ site.site_name }}</td>
              <td>{{ site.production_url }}</td>
              <td>{{ site.staging_url }}</td>
              <td>{{ site.custodian }}</td>
              <td>
                <b-button variant="success">Create Editor</b-button>
              </td>
            </tr>
          </tbody>
        </table>
          </b-card-text>
        </b-tab>
        <b-tab>
          <template slot="title">
            Edit Sessions <b-badge pill> {{edit_sessions.length}} </b-badge>
          </template>
          <b-card-text>
            <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Session</th>
              <th scope="col">Site</th>
              <th scope="col">Creation Time</th>
              <th scope="col">Custodian</th>
              <th scope="col">Production</th>
              <th scope="col">Staging</th>
              <th scope="col">Admin</th>
              <th scope="col">Build</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(session, index) in edit_sessions" :key="index">
              <td>{{ session.session_id }}</td>
              <td>{{ session.site_name }}</td>
              <td>{{ session.creation_time }}</td>
              <td>{{ session.custodian }}</td>
              <td>{{ session.production_url }}</td>
              <td>{{ session.staging_url }}</td>
              <td>{{ session.admin_url }}</td>
              <td>{{ session.build_url }}</td>
              <td>
                <b-button variant="primary">Park</b-button>
                <b-button variant="danger">Destroy</b-button>
                <b-button variant="dark">Stage</b-button>
                <b-button variant="success">Request release</b-button>
              </td>
            </tr>
          </tbody>
        </table>
          </b-card-text>
        </b-tab>
        <b-tab title="Parked Sessions">
          <template slot="title">
            Parked Sessions <b-badge pill> {{parked_sessions.length}} </b-badge>
          </template>
          <b-card-text>
            <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Session</th>
              <th scope="col">Site</th>
              <th scope="col">Creation Time</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(session, index) in parked_sessions" :key="index">
              <td>{{ session.session_id }}</td>
              <td>{{ session.site_name }}</td>
              <td>{{ session.creation_time }}</td>
              <td>
                <b-button variant="primary">Unpark</b-button>
                <b-button variant="danger">Destroy</b-button>
              </td>
            </tr>
          </tbody>
        </table>
          </b-card-text>
        </b-tab>
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
      available_sites: [],
      edit_sessions: [],
      parked_sessions: [],
    };
  },
  methods: {
    getAvailableSites() {
      const path = 'http://localhost:5000/sites';
      axios.get(path)
        .then((res) => {
          this.available_sites = res.data;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    getEditSessions() {
      const path = 'http://localhost:5000/edits';
      axios.get(path)
        .then((res) => {
          this.edit_sessions = res.data;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    getParkedSessions() {
      const path = 'http://localhost:5000/parked';
      axios.get(path)
        .then((res) => {
          this.parked_sessions = res.data;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
  },
  created() {
    this.getAvailableSites();
    this.getEditSessions();
    this.getParkedSessions();
  },
};
</script>

<style>

</style>
