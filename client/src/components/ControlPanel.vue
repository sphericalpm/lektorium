<template>
  <div>
    <alert :message=message v-if="showMessage"></alert>
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
              <td>{{ site.siteName }}</td>
              <td>{{ site.productionUrl }}</td>
              <td>{{ site.stagingUrl }}</td>
              <td>{{ site.custodian }}</td>
              <td>
                <b-button variant="success" @click="createSession(site)">Create Editor</b-button>
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
              <td>{{ session.sessionId }}</td>
              <td>{{ session.siteName }}</td>
              <td>{{ session.creationTime }}</td>
              <td>{{ session.custodian }}</td>
              <td>{{ session.productionUrl }}</td>
              <td>{{ session.stagingUrl }}</td>
              <td>{{ session.editUrl }}</td>
              <td>{{ session.viewUrl }}</td>
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
              <td>{{ session.sessionId }}</td>
              <td>{{ session.siteName }}</td>
              <td>{{ session.creationTime }}</td>
              <td>
                <b-button variant="primary">Unpark</b-button>
                <b-button variant="danger" @click="destroySession(session)">Destroy</b-button>
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
import Alert from './Alert.vue';
import { stat } from 'fs';

export default {
  name: 'ControlPanel',
  data() {
    return {
      available_sites: [],
      edit_sessions: [],
      parked_sessions: [],
      message: '',
      showMessage: false,
      destroy_status: '',
    };
  },
  components: {
    alert: Alert,
  },
  methods: {
    async getPanelData() {
      var result = await axios({
        method: "POST",
        url: "/graphql",
        data: {
          query: `
              {
                sites {
                  siteId
                  custodian
                  custodianEmail
                  productionUrl
                  siteName
                  stagingUrl
                }
                editSessions: sessions {
                  sessionId
                  siteName
                  creationTime
                  custodian
                  productionUrl
                  stagingUrl
                  editUrl
                  viewUrl
                }
                parkedSessions: sessions(parked: true) {
                  sessionId
                  siteName
                  creationTime
                }
              }
          `
        }
      });
      this.available_sites = result.data.data.sites;
      this.edit_sessions = result.data.data.editSessions;
      this.parked_sessions = result.data.data.parkedSessions;
    },
    async destroySession(session) {
      let id = session.sessionId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        data: {
          query: `
                mutation {
                destroySession(sessionId: "${id}") {
                  ok
                }
              }
          `
        }
      });
      if(result.data.data.destroySession.ok)
      {
        this.message = `'${id}' removed successfully.`;
        this.showMessage = true;
        this.getPanelData();
      }
    },
    async createSession(site) {
      let id = site.siteId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        data: {
          query: `
                mutation {
                createSession(siteId: "${id}") {
                  ok
                }
              }
          `
        }
      });
      if(result.data.data.createSession.ok)
      {
        this.message = `Session created successfully.`;
        this.showMessage = true;
        this.getPanelData();
      }
    },
  },
  created() {
    this.getPanelData();
  },
};
</script>

<style>

</style>
