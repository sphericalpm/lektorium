<template>
  <div v-shortkey="['shift', 'o']" @shortkey="changeHiddenButton">
    <loading :active.sync="loading_overlay_active" :is-full-page="true"></loading>
    <b-card no-body>
      <b-tabs pills card vertical v-model="current_tab">
        <b-tab @click="refreshPanelData">
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
                      <b-button
                        class="rounded"
                        variant="success"
                        v-b-modal.site-modal
                        v-if="create_site_btn_visible"
                      >+ Create New Site</b-button>
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
                      target="_blank"
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
                        class="rounded"
                        variant="success"
                        @click="createSession(site)"
                        :disabled="checkActiveSession(site)"
                      >Create Editor</b-button>
                  </td>
                </tr>
              </tbody>
            </table>
          </b-card-text>
        </b-tab>
        <b-tab @click="refreshPanelData">
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
                  <td>{{ convertTime(session.creationTime) }}</td>
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
                      target="_blank"
                    >{{ session.editUrl }}</a>
                    <span v-else>{{ session.editUrl }}</span>
                  </td>
                  <td>{{ session.viewUrl }}</td>
                  <td>
                    <b-button-group>
                      <b-button
                        class="rounded mb-1 mr-1"
                        variant="primary"
                        @click="parkSession(session)"
                      >Park</b-button>
                      <b-button
                        class="rounded mb-1 mr-1"
                        variant="danger"
                        @click="destroySession(session)"
                      >Destroy</b-button>
                      <b-button
                        class="rounded mb-1 mr-1"
                        variant="success"
                        @click="requestRelease(session)"
                      >Request release</b-button>
                    </b-button-group>
                  </td>
                </tr>
              </tbody>
            </table>
          </b-card-text>
        </b-tab>
        <b-tab @click="refreshPanelData">
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
                  <td>{{ convertTime(session.creationTime) }}</td>
                  <td>
                    <b-button-group>
                      <b-button
                        class="rounded mb-1 mr-1"
                        variant="primary"
                        @click="unparkSession(session)"
                        :disabled="checkUnparkedSessions(session)"
                      >Unpark</b-button>
                      <b-button
                        class="rounded mb-1 mr-1"
                        variant="danger"
                        @click="destroySession(session)"
                      >Destroy</b-button>
                    </b-button-group>
                  </td>
                </tr>
              </tbody>
            </table>
          </b-card-text>
        </b-tab>
        <b-tab @click="refreshPanelData">
          <template slot="title">
            Releasing <b-badge pill> {{releasing.length}} </b-badge>
          </template>
          <b-card-text>
            <table class="table table-hover">
              <thead>
                <tr>
                  <th scope="col">Session ID</th>
                  <th scope="col">Site Name</th>
                  <th scope="col">Merge Request</th>
                  <th scope="col">State</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(release, index) in releasing" :key="index">
                  <td>{{ release.sourceBranch }}</td>
                  <td>{{ release.siteName }}</td>
                  <td>
                    <a v-if="release.webUrl.startsWith('http')"
                      :href="release.webUrl"
                      target="_blank"
                    >{{ release.title }}</a>
                  </td>
                  <td>{{ release.state }}</td>
                </tr>
              </tbody>
            </table>
          </b-card-text>
        </b-tab>
        <b-tab @click="refreshPanelData" title="Users">
          <template slot="title">
            Users <b-badge pill>{{users.length}}</b-badge>
          </template>
          <b-card-text>
            <table class="table table-hover">
              <thead>
                <tr>
                  <th scope="col">User ID</th>
                  <th scope="col">Nickname</th>
                  <th scope="col">Name</th>
                  <th scope="col">Email</th>
                  <th scope="col"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(user, index) in users" :key="index">
                  <td>{{ user.userId }}</td>
                  <td>{{ user.nickname }}</td>
                  <td>{{ user.name }}</td>
                  <td> {{ user.email }} </td>
                  <td>
                    <b-button v-b-modal.user-modal @click="showUserModal(user.userId)">Permissions</b-button>
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
      @hidden="onReset"
      hide-footer>
      <b-form @submit="onSubmit" @reset="onReset" class="w-100">
        <b-form-group
          id="form-title-group"
          label="Title:"
          label-for="form-title-input">
          <b-form-input
            id="form-title-input"
            type="text"
            v-model="add_site_form.title"
            required
            placeholder="Enter title"></b-form-input>
        </b-form-group>
        <b-form-group
          id="form-id-group"
          label="Site id:"
          label-for="form-id-input">
          <b-form-input
            id="form-id-input"
            type="text"
            v-model="add_site_form.site_id"
            required
            placeholder="Enter site id"></b-form-input>
        </b-form-group>
        <b-button-group>
          <b-button class="rounded mb-1 mr-1" type="submit" variant="primary">OK</b-button>
          <b-button class="rounded mb-1 mr-1" type="reset" variant="danger">Cancel</b-button>
        </b-button-group>
      </b-form>
    </b-modal>
    <b-modal
    id="user-modal"
    :title="userModalData.userId"
    hide-footer
    @hidden="initUserModal">
      <b-form class="mb-3" inline>
        <b-form-group label="Permissions:">
          <b-form-checkbox-group id="checkbox-group-permissions" v-model="selected" name="permissions-2">
            <b-form-checkbox v-for="(permission, index) in availablePermissions" :key="index" :value="permission.value">
              {{permission.value}}
            </b-form-checkbox>
          </b-form-checkbox-group>
        </b-form-group>
      </b-form>
      <div class="text-center">
        <b-button variant="success">
          Save
        </b-button>
      </div>
    </b-modal>
    <b-alert
      :show="message_visible"
      :variant="message_type"
      dismissible @dismissed="message_visible=false"
    >{{ message }}</b-alert>
  </div>
</template>

<script>
import axios from 'axios';
import Alert from './Alert.vue';
import Loading from 'vue-loading-overlay';
import 'vue-loading-overlay/dist/vue-loading.css';

export default {
  name: 'ControlPanel',
  data() {
    return {
      available_sites: [],
      edit_sessions: [],
      parked_sessions: [],
      users: [],
      userModalData: {
        userId:'',
        permissions: {},
        },
      availablePermissions: [],
      selectedPermissions: [],
      releasing: [],

      add_site_form: {
        title: '',
        site_id: '',
      },

      create_site_btn_visible: false,
      current_tab: 0,
      loading_overlay_active: false,

      message: '',
      message_visible: false,
      message_type: 'success',
    };
  },
  components: {
    alert: Alert,
    Loading,
  },
  methods: {

    async getHeaders() {
      if (this.$auth === undefined) return {};
      const tokens = await this.$auth.getTokens();
      return {Authorization: `Bearer ${tokens.join('.')}`};
    },

    startLoadingModal() {
      const delay = 800;
      let timer_id = setTimeout(() => this.loading_overlay_active = true, delay);
      return timer_id;
    },

    finishLoadingModal(timer_id) {
      clearTimeout(timer_id);
      this.loading_overlay_active = false;
    },

    async makeRequest(query) {
      let timer_id = this.startLoadingModal();
      var result = await axios({
        method: "POST",
        url: "/graphql",
        headers: await this.getHeaders(),
        data: {
          query: query
        }
      });
      this.finishLoadingModal(timer_id);
      return result;
    },

    refreshPanelData() {
      this.getPanelData();
      this.message_visible = false;
    },

    async getPanelData() {
      let query = `
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
                users {
                  nickname
                  name
                  email
                  userId
                }
                releasing {
                  id
                  title
                  state
                  siteName
                  sourceBranch
                  webUrl
                }
              }
          `;
      let result = await this.makeRequest(query);
      this.available_sites = result.data.data.sites;
      this.edit_sessions = result.data.data.editSessions;
      this.parked_sessions = result.data.data.parkedSessions;
      this.users = result.data.data.users;
      this.releasing = result.data.data.releasing;
      this.checkStarting();
    },

    async destroySession(session) {
      let id = session.sessionId;
      let query = `
                mutation {
                destroySession(sessionId: "${id}") {
                  ok
                }
              }
          `;
      let result = await this.makeRequest(query);
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
      let query = `
                mutation {
                parkSession(sessionId: "${id}") {
                  ok
                }
              }
          `;
      let result = await this.makeRequest(query);
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
      let query = `
                mutation {
                unparkSession(sessionId: "${id}") {
                  ok
                }
              }
          `;
      let result = await this.makeRequest(query);
      if(result.data.data.unparkSession.ok)
      {
        this.showMessage(`'${id}' unparked successfully.`,`success`);
        this.current_tab = 1;
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to unpark '${id}'`, `danger`);
      }
    },

    async requestRelease(session) {
      let id = session.sessionId;
      let query = `
                mutation {
                requestRelease(sessionId: "${id}") {
                  ok
                }
              }
          `;
      const result = await this.makeRequest(query);
      const data = result.data;
      if(data.errors)
      {
        const message = data.errors[0].message;
        this.showMessage(`Error: ${message}`, `danger`);
      }
      else if(data.requestRelease.ok)
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
      let query = `
                mutation {
                createSession(siteId: "${id}") {
                  ok
                }
              }
          `;
      let result = await this.makeRequest(query);
      if(result.data.data.createSession.ok)
      {
        this.showMessage(`Session created successfully.`, `success`);
        this.getPanelData();
        this.current_tab = 1;
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
      let query = `
                mutation {
                createSite(
                  siteId: "${site_id}",
                  siteName: "${site_name}",
                )
                {
                  ok
                }
              }
          `;
      var result = await this.makeRequest(query);
      if(result.data.data.createSite.ok) {
        this.showMessage(`${site_name} was created`, `success`);
        this.getPanelData();
      }
      else {
        this.showMessage(`Unable to create site`, `danger`);
      }
    },

    async getUserPermissions(userId) {
      let query = `
        {
          permissions(userId: "${userId}") {
            permissionName
            description
          }
        }
      `;
      let result = await this.makeRequest(query);
      this.userModalData['permissions'] = result.data.data.permissions;
    },

    async setUserPermissions(userId, permissions) {
      let query = `
                mutation {
                setUserPermissions(userId: "${userId}", permissions: "${permissions}") {
                  ok
                }
              }
          `;
      let result = await this.makeRequest(query);
      if(result.data.data.setUserPermissions.ok) {
        this.refreshUserModal(userId);
      }
      else {
        this.showMessage(`Unable to add permisson`, `danger`);
      }
    },

    async deleteUserPermissions(userId, permissions) {
      let query = `
                mutation {
                deleteUserPermissions(userId: "${userId}", permissions: "${permissions}") {
                  ok
                }
              }
          `;
      let result = await this.makeRequest(query);
      if(result.data.data.deleteUserPermissions.ok) {
        this.refreshUserModal(userId);
      }
      else {
        this.showMessage(`Unable to remove permisson`, `danger`);
      }
    },

    async getAvailablePermissions() {
      let query = `
        {
          availablePermissions {
            value
          }
        }
      `;
      let result = await this.makeRequest(query);
      this.availablePermissions = result.data.data.availablePermissions;
    },

    showMessage(text, type) {
      this.message = text;
      this.message_type = type;
      this.message_visible = true;
    },

    showUserModal(userId) {
      this.initUserModal();
      this.userModalData.userId = userId;
      this.getUserPermissions(userId);
      this.getAvailablePermissions();
      this.$bvModal.show(`user-modal`);
    },

    initUserModal() {
      this.selectedPermissions = [];
      this.userModalData.userId = '';
      this.userModalData.permissions = [];
      this.availablePermissions = [];

    },

    refreshUserModal(userId) {
      this.selectedPermissions = [];
      this.userModalData.permissions = [];
      this.availablePermissions = [];
      this.getUserPermissions(userId);
      this.getAvailablePermissions();
    },

    initForm() {
      this.add_site_form.title = '';
      this.add_site_form.site_id = '';
    },

    onSubmit(evt) {
      evt.preventDefault();
      this.$refs.addSiteModal.hide();
      const payload = {
        title: this.add_site_form.title,
        site_id: this.add_site_form.site_id,
      };
      this.addSite(payload);
      this.initForm
    },

    onReset(evt) {
      evt.preventDefault();
      this.$refs.addSiteModal.hide();
      this.initForm();
    },

    changeHiddenButton() {
      this.create_site_btn_visible = !this.create_site_btn_visible;
    },

    checkStarting() {
      let production_result = this.available_sites.find(item => item.productionUrl == "Starting");
      let admin_result = this.edit_sessions.find(item => item.editUrl == "Starting");
      let view_result = this.edit_sessions.find(item => item.viewUrl == "Starting");
      if(admin_result || production_result || view_result){
        setTimeout(this.getPanelData,5000);
      }
    },

    convertTime(time) {
      let utc_time = new Date(time);
      utc_time.setMinutes(utc_time.getMinutes()-utc_time.getTimezoneOffset());
      const user_time = utc_time.toLocaleString();
      return user_time;
    },

  },

created() {
    this.getPanelData();
  },
};
</script>

<style>
  .rounded
  {
    border-radius: 10px;
  }

  .modal-backdrop
  {
      opacity:0.5 !important;
  }
</style>
