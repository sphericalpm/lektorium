<template>
    <div class="container">
        <div class="row align-items-center profile-header">
            <div class="col-md-2 mb-3">
                <img
                    :src="profile.picture"
                    alt="User's profile picture"
                    class="rounded-circle img-fluid profile-picture"
                />
            </div>
            <div class="col-md text-center text-md-left">
                <h2>{{ profile.name }}</h2>
                <p class="lead text-muted">{{ profile.email }}</p>
            </div>
        </div>

        <div class="row">
            <pre v-highlightjs class="rounded w-100">
                <code class="json">{{ JSON.stringify(profile, null, 4) }}</code>
            </pre>
        </div>
    </div>
</template>

<script>
module.exports = {
    computed: {
        profile() {
            return this.$auth.profile;
        },
    },
    directives: {
        highlightjs: {
            deep: true,
            bind: el => _.map(el.querySelectorAll('code'), hljs.highlightBlock),
        },
    },
};
</script>
