<template>
    <pre>{{ logs }}</pre>
</template>
<script>
module.exports = {
    computed: {
        container: () => new URLSearchParams(window.location.search).get('container'),
    },
    asyncComputed: {
        async headers() {
            if (this.$auth === undefined) return {};
            const tokens = await this.$auth.getTokens();
            return {Authorization: `Bearer ${tokens.join('.')}`};
        },

        async logs() {
            if (!_.isNil(this.headers)) {
                let container = this.container || 'lektorium';
                var result = await axios({
                    method: "POST",
                    url: "/graphql",
                    headers: await this.headers,
                    data: {
                        query: `{logs(container: "${container}")}`
                    }
                });
                if (_.isEmpty(result.data.data.logs)) {
                    return _(result.data.errors).map('message').join('\n');
                };
                return result.data.data.logs;
            };
        },
    },
};
</script>
