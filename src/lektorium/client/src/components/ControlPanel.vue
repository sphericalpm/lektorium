<template>
  <div v-shortkey="['f9']" @shortkey="changeHiddenButton">
    <b-card no-body>
      <b-tabs pills card vertical v-model="tab_index">
        <b-tab @click="getPanelData(); is_message_visible = false;">
          <template slot="title">
            Available Sites <b-badge pill> {{available_sites.length}} </b-badge>
          </template>
          <b-card-text>
            <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Site</th>
              <th scope="col">Production</th>
              <!-- <th scope="col">Staging</th> -->
              <th scope="col">Custodian</th>
              <th>
                <div class="text-right">
                  <b-button variant="success" v-b-modal.site-modal v-if="is_hidden_btn_visible">
                    + Create New Site
                  </b-button>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(site, index) in available_sites" :key="index">
              <td>{{ site.siteName }}</td>
              <td>
                <a
                  v-if="site.productionUrl.startsWith('http')"
                  :href="site.productionUrl"
                >{{ site.productionUrl }}</a>
                <span v-else>{{ site.productionUrl }}</span>
              </td>
              <!-- <td> <a :href="site.stagingUrl">{{ site.stagingUrl }}</a></td> -->
              <td>
                <a :href="'mailto:' + site.custodianEmail">
                  {{ site.custodian }}
                </a>
              </td>
              <td>
                  <b-button
                  variant="success"
                  @click="createSession(site)"
                  :disabled="checkActiveSession(site)">
                      Create Editor
                  </b-button>
              </td>
            </tr>
          </tbody>
        </table>
          </b-card-text>
        </b-tab>
        <b-tab @click="getPanelData(); is_message_visible = false;">
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
              <!-- <th scope="col">Production</th> -->
              <!-- <th scope="col">Staging</th> -->
              <th scope="col">Admin</th>
              <th scope="col">Build</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(session, index) in edit_sessions" :key="index">
              <td>{{ session.sessionId }}</td>
              <td>{{ session.siteName }}</td>
              <td>{{ session.creationTime | moment("MM/DD/YY, hh:mm") }}</td>
              <td>
                <a :href="'mailto:' + session.custodianEmail">
                  {{ session.custodian }}
                </a>
              </td>
              <!-- <td>{{ session.productionUrl }}</td> -->
              <!-- <td>{{ session.stagingUrl }}</td> -->
              <td>
                <a
                  v-if="session.editUrl.startsWith('http')"
                  :href="session.editUrl"
                >{{ session.editUrl }}</a>
                <span v-else>{{ session.editUrl }}</span>
              </td>
              <td>{{ session.viewUrl }}</td>
              <td>
                <b-button variant="primary" @click="parkSession(session)">Park</b-button>
                <b-button variant="danger" @click="destroySession(session)">Destroy</b-button>
                <!-- <b-button variant="dark" @click="stage(session)">Stage</b-button> -->
                <b-button variant="success" @click="requestRelease(session)">Request release</b-button>
              </td>
            </tr>
          </tbody>
        </table>
          </b-card-text>
        </b-tab>
        <b-tab @click="getPanelData(); is_message_visible = false;" title="Parked Sessions">
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
              <td>{{ session.creationTime | moment("MM/DD/YY, hh:mm") }}</td>
              <td>
                <b-button
                variant="primary"
                @click="unparkSession(session)"
                :disabled="checkUnparkedSessions(session)">
                  Unpark
                </b-button>
                <b-button variant="danger" @click="destroySession(session)">Destroy</b-button>
              </td>
            </tr>
          </tbody>
        </table>
          </b-card-text>
        </b-tab>
      </b-tabs>
    </b-card>
    <b-modal
      ref="addSiteModal"
      id="site-modal"
      title="Create new site"
      hide-footer>
      <b-form @submit="onSubmit" @reset="onReset" class="w-100">
        <b-form-group
        id="form-title-group"
          label="Title:"
          label-for="form-title-input">
          <b-form-input
            id="form-title-input"
            type="text"
            v-model="addSiteForm.title"
            required
            placeholder="Enter title">
          </b-form-input>
        </b-form-group>
        <b-form-group
          id="form-id-group"
          label="Site id:"
          label-for="form-id-input">
          <b-form-input
            id="form-id-input"
            type="text"
            v-model="addSiteForm.site_id"
            required
            placeholder="Enter site id">
          </b-form-input>
        </b-form-group>
        <b-button type="submit" variant="primary">OK</b-button>
        <b-button type="reset" variant="danger">Cancel</b-button>
      </b-form>
    </b-modal>
    <alert :message=message v-if="showMessage"></alert>
  </div>
</template>

<script>
import axios from 'axios';
import Alert from './Alert.vue';

export default {
  name: 'ControlPanel',
  data() {
    return {
      addSiteForm: {
        title: '',
        site_id: '',
      },
      available_sites: [],
      edit_sessions: [],
      parked_sessions: [],
      message: '',
      is_message_visible: false,
      is_hidden_btn_visible: false,
      message_type: 'success',
      destroy_status: '',
      tab_index: 0,
    };
  },
  components: {
    alert: Alert,
  },
  methods: {

    async getHeaders() {
      if (this.$auth ===undefined) return {};
      const tokens = await this.$auth.getTokens();
      return {Authorization: `Bearer ${tokens.join('.')}`};
    },

    async getPanelData() {
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
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
                  sessions {
                    parked
                  }
                }
                editSessions: sessions {
                  sessionId
                  siteName
                  creationTime
                  custodian
                  custodianEmail
                  productionUrl
                  stagingUrl
                  editUrl
                  viewUrl
                  site {
                    siteId
                  }
                }
                parkedSessions: sessions(parked: true) {
                  sessionId
                  siteName
                  creationTime
                  site {
                    siteId
                  }
                }
              }
          `
        }
      });
      this.available_sites = result.data.data.sites;
      this.edit_sessions = result.data.data.editSessions;
      this.parked_sessions = result.data.data.parkedSessions;
      this.checkStarting();
    },

    async destroySession(session) {
      let id = session.sessionId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
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
      if(result.data.data.destroySession.ok) {
        this.showMessage(`'${id}' removed successfully.`, `success`);
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to remove '${id}'`, `danger`);
      }
    },

    async parkSession(session) {
      let id = session.sessionId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
        data: {
          query: `
                mutation {
                parkSession(sessionId: "${id}") {
                  ok
                }
              }
          `
        }
      });
      if(result.data.data.parkSession.ok)
      {
        this.showMessage(`'${id}' parked successfully.`,`success`);
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to park '${id}'`, `danger`);
      }
    },

    async unparkSession(session) {
      let id = session.sessionId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
        data: {
          query: `
                mutation {
                unparkSession(sessionId: "${id}") {
                  ok
                }
              }
          `
        }
      });
      if(result.data.data.unparkSession.ok)
      {
        this.showMessage(`'${id}' unparked successfully.`,`success`);
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to unpark '${id}'`, `danger`);
      }
    },

    async stage(session) {
      let id = session.sessionId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
        data: {
          query: `
                mutation {
                stage(sessionId: "${id}") {
                  ok
                }
              }
          `
        }
      });
      if(result.data.data.stage.ok)
      {
        this.showMessage(`'${id}' staged.`, `success`);
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to stage '${id}'`, `danger`);
      }
    },

    async requestRelease(session) {
      let id = session.sessionId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
        data: {
          query: `
                mutation {
                requestRelease(sessionId: "${id}") {
                  ok
                }
              }
          `
        }
      });
      if(result.data.data.requestRelease.ok)
      {
        this.showMessage(`Release request was sent.`, `success`);
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to send release request`, `danger`);
      }
    },

    async createSession(site) {
      let id = site.siteId;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
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
        this.showMessage(`Session created successfully.`, `success`);
        this.getPanelData();
        this.tab_index = 1;
      }
      else {
        this.showMessage(`Unable to create session`, `danger`);
      }
    },

    checkActiveSession(site) {
      let result = false;
      if (site.sessions) {
        result = site.sessions.find(item => item.parked == false);
      }
      return Boolean(result);
    },

    checkUnparkedSessions(session) {
      let result = false;
      const siteId = session.site.siteId;
      result = this.edit_sessions.find(item => item.site.siteId == siteId);
      return Boolean(result);
    },

    async addSite(payload) {
      const site_name = payload.title;
      const site_id = payload.site_id;
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
        data: {
          query: `
                mutation {
                createSite(
                  siteId: "${site_id}",
                  siteName: "${site_name}",
                )
                {
                  ok
                }
              }
          `
        }
      });
      if(result.data.data.createSite.ok) {
        this.showMessage(`${site_name} was created`, `success`);
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to create site`, `danger`);
      }
    },

    showMessage(text, type) {
      this.message = text;
      this.message_type = type;
      this.is_message_visible = true;
    },

    initForm() {
      this.addSiteForm.title = '';
      this.addSiteForm.site_id = '';
    },

    onSubmit(evt) {
      evt.preventDefault();
      this.$refs.addSiteModal.hide();
      const payload = {
        title: this.addSiteForm.title,
        site_id: this.addSiteForm.site_id,
      };
      this.addSite(payload);
      this.initForm
    },

    onReset(evt) {
      evt.preventDefault();
      this.$refs.addSiteModal.hide();
      this.initForm();
    },
    changeHiddenButton(event) {
      this.is_hidden_btn_visible = !this.is_hidden_btn_visible;
    },

    checkStarting() {
      let production_result = this.available_sites.find(item => item.productionUrl == "Starting");
      let admin_result = this.edit_sessions.find(item => item.editUrl == "Starting");
      let view_result = this.edit_sessions.find(item => item.viewUrl == "Starting");
      if(admin_result || production_result || production_result){
        setTimeout(this.getPanelData,5000);
      }
    },
  },

created() {
    this.getPanelData();
  },
};
</script>

<style>
  .modal-backdrop
  {
      opacity:0.5 !important;
  }
</style>
