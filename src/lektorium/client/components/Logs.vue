<template>
    <pre>{{ logs }}</pre>
</template>
<script>
module.exports = {
    asyncComputed: {
        async headers() {
            if (this.$auth === undefined) return {};
            const tokens = await this.$auth.getTokens();
            return {Authorization: `Bearer ${tokens.join('.')}`};
        },

        async logs() {
            if (!_.isNil(this.headers)) {
                var result = await axios({
                    method: "POST",
                    url: "/graphql",
                    headers: await this.headers,
                    data: {
                        query: '{logs}'
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
