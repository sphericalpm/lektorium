<template>
    <div class="nav-container mb-3">
        <nav class="navbar navbar-expand-md navbar-light bg-light">
            <div class="container nav-bar-fix">
                <div class="navbar-brand logo"></div>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav mr-auto">
                        <li class="nav-item">
                            <router-link to="/" class="nav-link">Lektorium</router-link>
                        </li>
                    </ul>
                    <div class="login-controls">
                    <ul class="navbar-nav d-none d-md-block">
                        <li v-if="!isAuthenticated" class="nav-item">
                            <div v-if="anonymousMode">
                                <b-nav-item disabled right>
                                    Anonymous
                                </b-nav-item>
                            </div>
                            <div v-else>
                            <button
                                id="qsLoginBtn"
                                class="btn btn-primary btn-margin"
                                @click.prevent="login"
                            >Login</button>
                            </div>
                        </li>

                        <li class="nav-item dropdown" v-if="isAuthenticated">
                            <a
                                class="nav-link dropdown-toggle"
                                href="#"
                                id="profileDropDown"
                                data-toggle="dropdown"
                            >
                                <img
                                    :src="profile.picture"
                                    alt="User's profile picture"
                                    class="nav-user-profile rounded-circle"
                                    width="50"
                                />
                            </a>
                            <div class="dropdown-menu dropdown-menu-right">
                                <div class="dropdown-header">{{ profile.name }}</div>
                                <router-link to="/profile" class="dropdown-item dropdown-profile">
                                    <i class="mr-3 far fa-user"></i>Profile
                                </router-link>
                                <a id="qsLogoutBtn" href="#" class="dropdown-item" @click.prevent="logout">
                                    <i class="mr-3 far fa-power-off"></i>Log out
                                </a>
                            </div>
                        </li>
                    </ul>

                    <ul class="navbar-nav d-md-none" v-if="!isAuthenticated">
                        <button class="btn btn-primary btn-block" @click="login">Log in</button>
                    </ul>

                </div>
            </div>
        </nav>
    </div>
</template>

<script>
module.exports = {
    name: "NavBar",
    data() {
        return {
            isAuthenticated: false,
            profile: {},
        };
    },
    computed: {
        anonymousMode() {
            return !this.$auth;
        },
    },
    methods: {
        login() {
            this.$auth.login();
        },
        logout() {
            this.$auth.logOut();
            this.$router.push({ path: "/" });
        },
        handleLoginEvent(data) {
            this.isAuthenticated = data.loggedIn;
            this.profile = data.profile;
        },
    },
};
</script>

<style>
.nav-bar-fix {
    margin-left: 0px;
    margin-right: 0px;
    width: 100%;
    max-width: none;
}
.logo {
    background-image: url(/images/logo.svg);
}
</style>
