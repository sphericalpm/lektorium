<template>
    <pre>{{ logs }}</pre>
</template>
<script>
module.exports = {
    computed: {
        container: () => new URLSearchParams(window.location.search).get('container'),
        tail: () => new URLSearchParams(window.location.search).get('tail'),
    },
    asyncComputed: {
        async headers() {
            if (this.$auth === undefined) return {};
            const tokens = await this.$auth.getTokens();
            return {Authorization: `Bearer ${tokens.join('.')}`};
        },

        async logs() {
            if (!_.isNil(this.headers)) {
                let container = this.container || 'lektorium',
                    tail = this.tail || '200';
                var result = await axios({
                    method: "POST",
                    url: "/graphql",
                    headers: await this.headers,
                    data: {
                        query: `{logs(container: "${container}" tail: ${tail})}`
                    },
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
