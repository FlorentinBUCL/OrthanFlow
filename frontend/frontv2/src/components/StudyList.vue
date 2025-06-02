<template>
  <div class="study-list">
    <Search @search="searchStudies" />

    <div class="button-center">
      <button @click="getStudies" class="button-blue">Charging studies</button>
    </div>

    <div class="button-center">
      <button @click="toggleView('classic')" class="button-toggle" :class="{ active: currentView === 'classic' }">Radiological</button>
      <button @click="toggleView('wsi')" class="button-toggle" :class="{ active: currentView === 'wsi' }">Anapat</button>
    </div>

    <div v-if="filteredStudies.length === 0" class="no-data">No studies available</div>

    <table v-else class="study-table">
      <thead>
        <tr>
          <th>Selection</th>
          <th>Date</th>
          <th>Patient Name</th>
          <th>Description</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(study, index) in filteredStudies" :key="study._id || study.studyUID">
          <tr>
            <td>
              <input type="radio" :value="study" :name="selection" @change="selectItem(study)" />
            </td>
            <td>{{ study.date }}</td>
            <td>{{ study.PatientName }}</td>
            <td>{{ study.description }}</td>
            <td>
              <div class="actions">
                <button
                  v-for="action in study.links"
                  :key="action.label"
                  class="button-green"
                  @click="() => openAction(action)"
                >
                  {{ action.label }}
                </button>
                <button @click="toggleSeries(index)" class="button-red">
                  {{ expandedIndex.includes(index) ? 'Masquer les séries' : 'Afficher les séries' }}  
                </button>
              </div>
            </td>
          </tr>
            <tr v-if="expandedIndex.includes(index)">
            <td colspan="5">
              <StudyItem :study="study" @selectSerie="selectItem" />
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <Viewer v-if="selectedItem" :selectedItem="selectedItem" />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Search from "./Search.vue";
import StudyItem from "./StudyItem.vue";
import Viewer from "./Viewer.vue";

const studies = ref([]);
const filteredStudies = ref([]);
const selectedItem = ref(null);
const expandedIndex = ref([]);
const currentView = ref("classic");

const getStudies = async () => { // Function to fetch studies from the backend
  try {
    const res = await fetch("http://localhost:5000/studies");
    const result = await res.json();
    studies.value = result.Studies || [];
    applyFilter();
  } catch (error) {
    console.error("Error fetching studies :", error);
  }
};

const applyFilter = () => { // Function to apply the filter according to the type of image
  expandedIndex.value = [];
  filteredStudies.value = studies.value.filter((study) =>
    currentView.value === "classic" ? !study.is_wsi : study.is_wsi
  );
};

const toggleView = (viewType) => { // Function to toggle the view between classic and WSI
  currentView.value = viewType;
  applyFilter();
};

const searchStudies = async (query) => { // Function to search studies based on the query
  if (!query) {
    applyFilter();
    return;
  }
  try {
    const res = await fetch(`http://localhost:5000/search_studies?query=${encodeURIComponent(query)}`);
    const result = await res.json();
    const found = result.Studies || [];
    expandedIndex.value = [];
    filteredStudies.value = found.filter((study) =>
      currentView.value === "classic" ? !study.is_wsi : study.is_wsi
    );
  } catch (error) {
    console.error("Search error :", error);
  }
};

const toggleSeries = (index) => { // Function to show series for a study
  const idx = expandedIndex.value.indexOf(index);
  if (idx !== -1) {
    expandedIndex.value.splice(idx, 1); 
  } else {
    expandedIndex.value.push(index); 
  }
};


const openAction = (action) => { // Function to open an action link in a new tab
  window.open(action.url, "_blank");
};

const selectItem = (item) => { // Function to select an item 
  selectedItem.value = item;
};

onMounted(() => {
  getStudies();
});
</script>
