<template>
    <div>
        <loading :active.sync="loading_overlay_active" :is-full-page="true"></loading>
        <b-card no-body>
            <b-tabs pills card vertical v-model="current_tab">
                <b-tab @click="refreshPanelData">
                    <template slot="title">
                        Available Sites <b-badge pill> {{_.get(available_sites, 'length', 0)}} </b-badge>
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
                                                v-if="create_site_btn_visible"
                                                variant="success"
                                                class="rounded"
                                                v-b-modal.site-modal
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
                                        <b-dropdown
                                            :disabled="checkActiveSession(site)"
                                            text="Create Editor"
                                            right
                                            split
                                            variant="success"
                                            class="rounded"
                                            @click="createSession(site.siteId)"
                                        >
                                            <b-dropdown-item @click="customizeTheme(site.siteId)">Customize themes</b-dropdown-item>
                                        </b-dropdown>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </b-card-text>
                </b-tab>
                <b-tab @click="refreshPanelData">
                    <template slot="title">
                        Edit Sessions <b-badge pill> {{_.get(edit_sessions, 'length', 0)}} </b-badge>
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
                                    <th scope="col">Themes</th>
                                    <th scope="col">Admin</th>
                                    <th scope="col">Build</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(session, index) in edit_sessions" :key="index">
                                    <td>{{ session.sessionId }}</td>
                                    <td>{{ session.siteName }}</td>
                                    <td>{{ formatTime(session.creationTime) }}</td>
                                    <td>
                                        <a :href="'mailto:' + session.custodianEmail">
                                            {{ session.custodian }}
                                        </a>
                                    </td>
                                    <!-- <td>{{ session.productionUrl }}</td> -->
                                    <!-- <td>{{ session.stagingUrl }}</td> -->
                                    <td class="font-12">
                                        <template v-for="theme in session.themes">
                                            {{ theme }}<br>
                                        </template>
                                    </td>
                                    <td>
                                        <a
                                            v-if="session.editUrl && session.editUrl.startsWith('http')"
                                            :href="session.editUrl"
                                            target="_blank"
                                        >Admin&nbsp;Interface</a>
                                        <span v-else>{{ session.editUrl }}</span>

                                        <br>
                                        <a
                                            v-if="session.previewUrl && session.previewUrl.startsWith('http')"
                                            :href="session.previewUrl"
                                            target="_blank"
                                        >Site&nbsp;Preview</a>
                                        <span v-else-if="session.previewUrl">{{ session.previewUrl }}</span>
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
                        Parked Sessions <b-badge pill> {{_.get(parked_sessions, 'length', 0)}} </b-badge>
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
                                    <td>{{ formatTime(session.creationTime) }}</td>
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
                        Releasing <b-badge pill> {{_.get(releasing, 'length', 0)}} </b-badge>
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
                                    <td>{{ formatTime(release.creationTime) }}</td>
                                    <td>{{ release.state }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </b-card-text>
                </b-tab>
                <b-tab v-if="manage_users_visible" @click="refreshPanelData">
                    <template slot="title">
                        Users <b-badge pill>{{_.get(users, 'length', 0)}}</b-badge>
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
                                        <b-button v-b-modal.user-modal @click="showUserModal(user)">Edit Permissions</b-button>
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
            hide-footer
        >
            <b-form @submit="onSubmit" @reset="onReset" class="w-100">
                <b-form-group label="Title:">
                    <b-form-input
                        type="text"
                        v-model="add_site_form.title"
                        required
                        placeholder="Enter title"></b-form-input>
                </b-form-group>
                <b-form-group label="Site id:">
                    <b-form-input
                        type="text"
                        v-model="add_site_form.site_id"
                        required
                        placeholder="Enter site id"></b-form-input>
                </b-form-group>
                <b-form-group label="Owner:">
                    <b-form-input
                        list="owner-list"
                        v-model="add_site_form.owner"
                        placeholder="Select owner or leave empty to be an owner"></b-form-input>
                    <datalist id="owner-list">
                        <option v-for="u in users" :key="u" :value="`${u.email},${u.name}`">{{ u.name }}</option>
                    </datalist>
                </b-form-group>
                <b-form-group label="Themes:">
                    <theme-select v-model="add_site_form.themes"></theme-select>
                </b-form-group>
                <b-button-group>
                    <b-button class="rounded mb-1 mr-1" type="submit" variant="primary">OK</b-button>
                    <b-button class="rounded mb-1 mr-1" type="reset" variant="danger">Cancel</b-button>
                </b-button-group>
            </b-form>
        </b-modal>

        <b-modal
            v-if="!_.isNil(selectedUser)"
            id="user-modal"
            :title="selectedUser.name"
            hide-footer
            @hidden="initUserModal"
        >
            <b-form class="mb-3">
                <b-form-group label="Permissions:">
                    <b-form-checkbox-group id="checkbox-group-permissions" v-model="selectedUserPermissions" name="permissions-2">
                        <templeate v-for="(permission, index) in availablePermissions" :key="index">
                            <b-form-checkbox :value="permission.value">
                                {{ getPermissionDescription(permission.value) }}
                            </b-form-checkbox>
                            <br>
                        </templeate>
                    </b-form-checkbox-group>
                </b-form-group>
            </b-form>
            <div class="text-center">
                <b-button variant="success" @click="updateUserPermissions"
                >Save</b-button>
            </div>
        </b-modal>

        <b-modal
            v-if="!_.isNil(selectedSite)"
            id="theme-select-modal"
            ref="themeSelectModal"
            title="Select themes and their load priority (use drag-and-drop)"
            hide-footer
            @hidden="resetThemeSelectModal"
        >
            <b-form class="mb-3">
                <b-form-group label="Themes:">
                    <theme-select
                        :site-id="selectedSite"
                        v-model="selectedThemes"
                        @ready="saveThemeBtnDisabled = !$event"
                    ></theme-select>
                </b-form-group>
            </b-form>
            <div class="text-center">
                <b-button
                    :disabled="saveThemeBtnDisabled"
                    variant="success"
                    @click="createThemedSession"
                >Save</b-button>
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
            selectedUser: undefined,
            userPermissions: [],
            selectedUserPermissions: [],
            releasing: [],
            selectedSite: undefined,
            selectedThemes: [],
            saveThemeBtnDisabled: true,

            add_site_form: {
                owner: '',
                title: '',
                site_id: '',
                themes: [],
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
        themeSelect: window.httpVueLoader('/components/ThemeSelect.vue'),
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
            } else {
                this.create_site_btn_visible = true;
                this.manage_users_visible = true;
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
                    previewUrl
                    themes
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
            let data = result.data.data;
            this.available_sites = data.sites;
            this.edit_sessions = this.convertTimeAndOrder(data.editSessions);
            this.parked_sessions = this.convertTimeAndOrder(data.parkedSessions);
            this.users = data.users;
            this.releasing = this.convertTimeAndOrder(data.releasing);
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

        async createThemedSession() {
            let themes = this.themesString(this.selectedThemes);
            let siteId = this.selectedSite;

            this.resetThemeSelectModal();
            this.$bvModal.hide('theme-select-modal');

            return await this.createSession(siteId, themes);
        },

        async createSession(siteId, themes='') {
            let query = `
                createSession(
                    siteId: "${siteId}",
                    ${themes}
                ) {
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
            const owner = _.isEmpty(payload.owner) ? '' : payload.owner;
            let query = `
                createSite(
                    siteId: "${payload.site_id}",
                    siteName: "${site_name}",
                    owner: "${owner}",
                    ${payload.themes}
                ) {
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
                this.deleteUserPermissions(this.selectedUser.userId, permissionsToDelete);
            }
            if (permissionsToSet.length>0){
                this.setUserPermissions(this.selectedUser.userId, permissionsToSet);
            }
            this.$bvModal.hide('user-modal');
        },

        getPermissionDescription(value) {
            if (!value.startsWith('user:')) {
                return value;
            };
            let site = _(this.available_sites).filter(x => x.siteId == value.slice(5)).head();
            return _.isNil(site) ? value : site.siteName;
        },

        showMessage(text, type) {
            this.message = text;
            this.message_type = type;
            this.message_visible = true;
        },

        showUserModal(user) {
            this.initUserModal();
            this.selectedUser = user;
            this.getUserPermissions(user.userId);
            this.$bvModal.show('user-modal');
        },

        initUserModal() {
            this.selectedUser = undefined;
            this.selectedUserPermissions = [];
            this.userPermissions = [];
        },

        customizeTheme(siteId) {
            this.resetThemeSelectModal()
            this.selectedSite = siteId;
            this.$nextTick(() => this.$bvModal.show('theme-select-modal'));
        },

        resetThemeSelectModal() {
            this.selectedSite = undefined;
            this.selectedThemes = [];
            this.saveThemeBtnDisabled = true;
        },

        refreshUserModal(userId) {
            this.selectedUserPermissions = [];
            this.userPermissions = [];
            this.getUserPermissions(userId);
        },

        initForm() {
            this.add_site_form.owner = '';
            this.add_site_form.title = '';
            this.add_site_form.site_id = '';
            this.add_site_form.themes = [];
        },

        onSubmit(evt) {
            evt.preventDefault();
            this.$refs.addSiteModal.hide();
            let hasThemes = (
                _.chain(this.add_site_form)
                .get('themes', [])
                .filter('active')
                .size()
                .value()
            ) > 0;

            this.addSite({
                title: this.add_site_form.title,
                site_id: this.add_site_form.site_id,
                owner: this.add_site_form.owner,
                themes: hasThemes ? this.themesString(this.add_site_form.themes) : '',
            });
            this.initForm();
        },

        onReset(evt) {
            evt.preventDefault();
            this.$refs.addSiteModal.hide();
            this.initForm();
        },

        checkStarting() {
            let production_result = _.find(this.available_sites, item => item.productionUrl == 'Starting');
            let admin_result = _.find(this.edit_sessions, item => item.editUrl == 'Starting');
            if (admin_result || production_result) {
                setTimeout(this.getPanelData,5000);
            }
        },

        formatTime(utc_time) {
            utc_time.setMinutes(utc_time.getMinutes()-utc_time.getTimezoneOffset());
            const user_time = utc_time.toLocaleString();
            return user_time;
        },

        convertTimeAndOrder(data) {
            return (
                _.chain(data)
                .map(item => ({...item, creationTime: new Date(item.creationTime)}))
                .orderBy(['creationTime'], ['desc'])
                .value()
            )
        },

        themesString(themes) {
            themes = (
                _.chain(themes)
                .filter('active')
                .map('name')
                .join('","')
                .value()
            );
            return themes ? `themes: ["${themes}"],` : 'themes: [],';
        },
    },

    asyncComputed: {
        async availablePermissions() {
            let query = `{
                availablePermissions {
                    value
                }
            }`;
            return (await this.makeRequest(query)).data.data.availablePermissions;
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

.font-12 {
    font-size: 12px;
}
</style>
