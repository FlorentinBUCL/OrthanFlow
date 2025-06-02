<template>
  <div v-if="series.length" class="series-container">
    <table class="series-list">
      <thead>
        <tr>
          <th>Selection</th>
          <th>Protocol</th>
          <th>Description</th>
          <th>Modality</th>
          <th>Operator</th>
          <th>Body part</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="serie in series" :key="serie.serieID">
          <td>
            <input type="radio" :value="serie" :name="'selection'" @change="$emit('selectSerie', serie)" /> 
          </td>
          <td>{{ serie.protocol }}</td>
          <td>{{ serie.description }}</td>
          <td>{{ serie.modality }}</td>
          <td>{{ serie.operator }}</td>
          <td>{{ serie.bodyPart }}</td>
          <td>
            <div class="actions">
              <button
                v-for="action in serie.links"
                :key="action.label"
                class="button-green"
                @click="() => openAction(action)"
              >
                {{ action.label }}
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps({
  study: Object,
});

const series = ref([]);

const fetchSeries = async () => { // Function for retrieving series from a study
  try {
    const res = await fetch(
      `http://localhost:5000/studies/${props.study._id}/series?study_uid=${props.study.studyUID}&is_wsi=${props.study.is_wsi}`
    );
    const data = await res.json();
    series.value = data.Series || [];
  } catch (err) {
    console.error("Error fetching series :", err);
  }
};

const openAction = (action) => { // Function to open an action link in a new tab
  window.open(action.url, "_blank");
};

onMounted(() => {
  fetchSeries();
});
</script>


