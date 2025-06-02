<template>
    <div class="search-container">
        <input
            type="text"
            v-model="query"
            @input="debouncedSearch"
            placeholder="Rechercher une étude"
            class="search-input"
        />
        <button v-if="query" @click="clearSearch" class="button-red">Effacer</button>
    </div>
</template>

<script setup>
import { ref } from "vue";
import { debounce } from "lodash";

const props = defineProps({ // Props for the search component
    initialQuery: { type: String, default: "" }
});

const emit = defineEmits(["search"]); // Emit event when search is performed
const query = ref(props.initialQuery); 


const debouncedSearch = debounce(() => { // function to handle search input
    console.log("Recherche envoyée :", query.value);
    emit("search", query.value);
}, 300);

const clearSearch = () => { // function to clear the search input
    query.value = "";
    emit("search", "");
};
</script>


