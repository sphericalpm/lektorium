<template>
    <div v-if="!_.isNil(usableThemes)">
        <b-table-simple class="table wo-borders" width="100%">
            <b-thead>
                <b-tr>
                    <b-td scope="col" width="10%">#</b-td>
                    <b-td scope="col" width="20%" class="text-right">Enabled</b-td>
                    <b-td scope="col" width="70%">Name</b-td>
                </b-tr>
            </b-thead>
            <b-tbody
                v-model="themes"
                is="draggable"
                tag="tbody"
            >
                <b-tr v-for="(themeData, idx) in themes" :key="idx">
                    <b-td>{{ idx + 1 }}</b-td>
                    <b-td class="text-right">
                        <b-form-checkbox
                            :name="`cbox-${idx}`"
                            :checked="themeData.active"
                            @input="(v) => themeData.active = v"
                        ></b-form-checkbox>
                    </b-td>
                    <b-td>{{ themeData.name }}</b-td>
                </b-tr>
            </b-tbody>
        </b-table-simple>
    </div>
    <div v-else class="text-center"><b-spinner></b-spinner></div>
</template>

<script>
module.exports = {
    props: {
        value: {
            type: Array,
        },
        siteId: {
            type: String,
            default: '',
        },
    },
    computed: {
        themes: {
            get() {
                return this.value;
            },
            set(items) {
                this.$emit('input', items);
            },
        },
    },
    methods: {
        async getHeaders() {
            if (this.$auth === undefined) return {};
            const tokens = await this.$auth.getTokens();
            return {Authorization: `Bearer ${tokens.join('.')}`};
        },
    },
    asyncComputed: {
        usableThemes() {
            let query = `
                {
                    themes(siteId: "${this.siteId}") {
                        name
                        active
                    }
                }
            `;
            return (
                this.getHeaders()
                .then(headers => (
                    axios({
                        method: "POST",
                        url: "/graphql",
                        headers: headers,
                        data: {query: query},
                    })
                ))
                .then(res => this.themes = _.get(res, 'data.data.themes'))
            );
        },
    },
    watch: {
        usableThemes(value) {
            this.$emit('ready', !_.isNil(value));
        },
    },
};
</script>

<style scoped>
thead td {
    text-transform: uppercase;
    opacity: 0.5;
    font-size: 12px;
}
</style>
