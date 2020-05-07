<template>
    <div>
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
                                            v-if="site.productionUrl && site.productionUrl.startsWith('http')"
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
                                            v-if="session.editUrl && session.editUrl.startsWith('http')"
                                            :href="session.editUrl"
                                            target="_blank"
                                        >{{ session.editUrl }}</a>
                                        <span v-else>{{ session.editUrl }}</span>
                                    </td>
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
                                    <th scope="col">Creation Time</th>
                                    <th scope="col">State</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(release, index) in releasing" :key="index">
                                    <td>{{ release.sourceBranch }}</td>
                                    <td>{{ release.siteName }}</td>
                                    <td>
                                        <a v-if="release.webUrl && release.webUrl.startsWith('http')"
                                            :href="release.webUrl"
                                            target="_blank"
                                        >{{ release.title }}</a>
                                    </td>
                                    <td>{{ convertTime(release.creationTime) }}</td>
                                    <td>{{ release.state }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </b-card-text>
                </b-tab>
                <b-tab v-if="manage_users_visible" @click="refreshPanelData">
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
                                    <th scope="col">Permissions</th>
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
                                        <ul>
                                            <li v-for="(permission, index) in user.permissions" :key="index">
                                                {{permission}}
                                            </li>
                                        </ul>
                                    </td>
                                    <td>
                                        <b-button v-b-modal.user-modal @click="showUserModal(user.userId)">Edit Permissions</b-button>
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
        :title="selectedUserId"
        hide-footer
        @hidden="initUserModal">
            <b-form class="mb-3">
                <b-form-group label="Permissions:">
                    <b-form-checkbox-group id="checkbox-group-permissions" v-model="selectedUserPermissions" name="permissions-2">
                        <b-form-checkbox v-for="(permission, index) in availablePermissions" :key="index" :value="permission.value">
                            {{permission.value}}
                        </b-form-checkbox>
                    </b-form-checkbox-group>
                </b-form-group>
            </b-form>
            <div class="text-center">
                <b-button variant="success" @click="updateUserPermissions">
                    Save
                </b-button>
            </div>
        </b-modal>
        <b-modal id="perm-alert" no-close-on-backdrop hide-header-close hide-footer title="Permission denied">
            <p>You do not have permission for this operation. Please, contact your system administrator.</p>
        </b-modal>
        <b-alert
            :show="message_visible"
            :variant="message_type"
            dismissible @dismissed="message_visible=false"
        >{{ message }}</b-alert>
    </div>
</template>

<script>
module.exports = {
    name: 'ControlPanel',
    data() {
        return {
            available_sites: [],
            edit_sessions: [],
            parked_sessions: [],
            users: [],
            selectedUserId: '',
            userPermissions: [],
            selectedUserPermissions: [],
            availablePermissions: [],
            releasing: [],

            add_site_form: {
                title: '',
                site_id: '',
            },

            create_site_btn_visible: false,
            manage_users_visible: false,
            current_tab: 0,
            loading_overlay_active: false,

            message: '',
            message_visible: false,
            message_type: 'success',
        };
    },
    components: {
        alert: window.httpVueLoader('/components/Alert.vue'),
        Loading: VueLoading,
    },
    methods: {
        isAnonymous(result) {
            if (result.data.errors !== undefined) {
                if (result.data.errors[0].code == 403){
                    return true;
                }
            }
            return false;
        },

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
            if (this.$auth !== undefined) {
                var permissions = this.$auth.profile.access_token.permissions;
                if (permissions.indexOf('admin') >= 0) {
                    this.create_site_btn_visible = true;
                    this.manage_users_visible = true;
                };
            };
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

        async makeMutationRequest(query, request_name) {
            let response = await this.makeRequest(`mutation {${query}}`);
            if (this.isAnonymous(response)) {
                this.$bvModal.show('perm-alert');
                return;
            };
            return [response.data.data[request_name], response.data.data.errors];
        },

        refreshPanelData() {
            this.getPanelData();
            this.message_visible = false;
        },

        async getPanelData() {
            let query = `{
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
                    permissions
                }
                releasing {
                    id
                    title
                    state
                    siteName
                    sourceBranch
                    webUrl
                    creationTime:createdAt
                }
            }`;
            let result = await this.makeRequest(query);
            if (this.isAnonymous(result)) {
                this.$bvModal.show('perm-alert');
                return;
            }
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
                destroySession(sessionId: "${id}") {
                    ok
                }
            `;
            const result = await this.makeMutationRequest(query, 'destroySession');
            if (result && result[0] && result[0].ok) {
                this.showMessage(`'${id}' removed successfully.`, `success`);
                this.getPanelData();
            } else {
                this.showMessage(`Unable to remove '${id}'`, `danger`);
            }
        },

        async parkSession(session) {
            let id = session.sessionId;
            let query = `
                parkSession(sessionId: "${id}") {
                    ok
                }
            `;
            const result = await this.makeMutationRequest(query, 'parkSession');
            if (result && result[0] && result[0].ok) {
                this.showMessage(`'${id}' parked successfully.`,`success`);
                this.getPanelData();
            } else {
                this.showMessage(`Unable to park '${id}'`, `danger`);
            }
        },

        async unparkSession(session) {
            let id = session.sessionId;
            let query = `
                unparkSession(sessionId: "${id}") {
                    ok
                }
            `;
            const result = await this.makeMutationRequest(query, 'unparkSession');
            if (result && result[0] && result[0].ok) {
                this.showMessage(`'${id}' unparked successfully.`,`success`);
                this.current_tab = 1;
                this.getPanelData();
            } else {
                this.showMessage(`Unable to unpark '${id}'`, `danger`);
            }
        },

        async requestRelease(session) {
            let id = session.sessionId;
            let query = `
                requestRelease(sessionId: "${id}") {
                    ok
                }
            `;
            const [result, errors] = await this.makeMutationRequest(query, 'requestRelease');
            if (errors) {
                this.showMessage(`Error: ${errors[0].message}`, `danger`);
            } else if (result && result.ok) {
                this.showMessage(`Release request was sent.`, `success`);
                this.current_tab = 3;
                this.getPanelData();
            } else {
                this.showMessage(`Unable to send release request`, `danger`);
            }
        },

        async createSession(site) {
            let id = site.siteId;
            let query = `
                createSession(siteId: "${id}") {
                    ok
                }
            `;
            const result = await this.makeMutationRequest(query, 'createSession');
            if (result && result[0] && result[0].ok) {
                this.showMessage(`Session created successfully.`, `success`);
                this.getPanelData();
                this.current_tab = 1;
            } else {
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
                createSite(siteId: "${site_id}", siteName: "${site_name}") {
                    ok
                }
            `;
            const result = await this.makeMutationRequest(query, 'createSite', 'create sites');
            if (result && result[0] && result[0].ok) {
                this.showMessage(`${site_name} was created`, `success`);
                this.getPanelData();
            } else {
                this.showMessage(`Unable to create site`, `danger`);
            }
        },

        async getUserPermissions(userId) {
            let query = `
                {
                    userPermissions(userId: "${userId}") {
                        permissionName
                        description
                    }
                }
            `;
            let result = await this.makeRequest(query);
            this.userPermissions = result.data.data.userPermissions;
            this.selectedUserPermissions = [];
            this.userPermissions.forEach(element => {
                this.selectedUserPermissions.push(element.permissionName)
            });
        },

        async setUserPermissions(userId, permissions) {
            let permissionsString = permissions.join('","');
            let query = `
                setUserPermissions(userId: "${userId}", permissions: ["${permissionsString}"]) {
                    ok
                }
            `;
            const result = await this.makeMutationRequest(query, 'setUserPermissions');
            if (result && result[0] && result[0].ok) {
                this.refreshUserModal(userId);
                this.refreshPanelData();
            } else {
                this.showMessage(`Unable to add permisson`, `danger`);
            }
        },

        async deleteUserPermissions(userId, permissions) {
            let permissionsString = permissions.join('","');
            let query = `
                deleteUserPermissions(userId: "${userId}", permissions: ["${permissionsString}"]) {
                    ok
                }
            `;
            const result = await this.makeMutationRequest(query, 'deleteUserPermissions');
            if (result && result[0] && result[0].ok) {
                this.refreshUserModal(userId);
                this.refreshPanelData();
            } else {
                this.showMessage(`Unable to remove permisson`, `danger`);
            }
        },

        async updateUserPermissions() {
            let permissionsToDelete = this.userPermissions.map(function(perm){return perm.permissionName});
            permissionsToDelete = permissionsToDelete.filter(element => !(this.selectedUserPermissions.includes(element)));
            let userPermissionsPlate = this.userPermissions.map(function(perm){return perm.permissionName});
            let permissionsToSet = this.selectedUserPermissions.filter(element => !(userPermissionsPlate.includes(element)));
            if (permissionsToDelete.length>0) {
                this.deleteUserPermissions(this.selectedUserId, permissionsToDelete);
            }
            if (permissionsToSet.length>0){
                this.setUserPermissions(this.selectedUserId, permissionsToSet);
            }
            this.$bvModal.hide(`user-modal`);
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
            this.selectedUserId = userId;
            this.getUserPermissions(userId);
            this.getAvailablePermissions();
            this.$bvModal.show(`user-modal`);
        },

        initUserModal() {
            this.selectedUserId = '';
            this.selectedUserPermissions = [];
            this.userPermissions = [];
            this.availablePermissions = [];

        },

        refreshUserModal(userId) {
            this.selectedUserPermissions = [];
            this.userPermissions = [];
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

        checkStarting() {
            let production_result = this.available_sites.find(item => item.productionUrl == "Starting");
            let admin_result = this.edit_sessions.find(item => item.editUrl == "Starting");
            if (admin_result || production_result) {
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

<style scoped>
.rounded {
    border-radius: 10px;
}

.modal-backdrop {
        opacity:0.5 !important;
}
</style>
