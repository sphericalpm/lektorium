<template>
    <div>
        <nav-bar></nav-bar>
        <div>
            <error></error>
            <div class="mt-5">
                <router-view></router-view>
            </div>
        </div>
    </div>
</template>

<script>
module.exports = {
    name: 'app',
    components: {
        'nav-bar': window.httpVueLoader('/components/NavBar.vue'),
        'error': window.httpVueLoader('/components/Error.vue')
    },
    created() {
        return this.$auth
        .handleAuthentication()
        .catch(() => this.$auth.login());
    },
};
</script>
