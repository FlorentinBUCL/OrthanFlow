<template>
  <div class="viewer-container" v-if="selectedItem">
    <h3>Choose a viewer :</h3>
    <div class="viewer-options">
      <label v-for="link in links" :key="link.name">
        <input
          type="radio"
          :value="link"
          v-model="selectedLink"
        />
        {{ link.label }}
      </label>
      
    </div>

    <div class="button-center">
      <button @click="submitSelection" class="button-blue">Select and generate the LTI link</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue';

const props = defineProps({
  selectedItem: Object // Can be a study or a series (must have 'links')
});
const selectedLink = ref(null);

// Link from selectedItem
const links = computed(() => props.selectedItem?.links || []);

// Resets the selection if the item changes
watchEffect(() => {
  selectedLink.value = null;
});

const submitSelection = async () => {
  if (!selectedLink.value) {
    alert("Please select a viewer !");
    return;
  }

  const sessionId = `session_${Date.now()}`;
  const makeTitle = () => { // Function to create a title based on the selected item and type of viewer
    const item = props.selectedItem;
    let nameTitle = item.is_study ? "Study" : "Serie";
      if(item.is_wsi) {
        nameTitle += " Anapathology";
      }
    return `${nameTitle} - ${item.description} - ${selectedLink.value.label}`;
  }

  try {
    const saveRes = await fetch("http://localhost:5000/save_session", { // Function to save the session with the selected viewer
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session: sessionId,
        viewer_url: selectedLink.value.url,
      }),
    });

    if (saveRes.ok) { // If the session is saved successfully, we create a form to submit the session ID and title to the backend
      const form = document.createElement("form");
      form.method = "POST";
      form.action = "http://localhost:5000/dl_submit";

      const sessionInput = document.createElement("input");
      sessionInput.type = "hidden";
      sessionInput.name = "session_id";
      sessionInput.value = sessionId;
      form.appendChild(sessionInput);

      const titleInput = document.createElement("input");
      titleInput.type = "hidden";
      titleInput.name = "title";
      titleInput.value = makeTitle();
      form.appendChild(titleInput);

      document.body.appendChild(form);
      form.submit();
    } else {
      console.error("Session registration error:");
    }
  } catch (error) {
    console.error("Selection error :", error);
  }
};

</script>
