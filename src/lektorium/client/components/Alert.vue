<template>
    <div>
        <b-alert variant="success" show dismissible>{{ message }}</b-alert>
        <br>
    </div>
</template>

<script>
module.exports = {
    props: ['message'],
};
</script>
