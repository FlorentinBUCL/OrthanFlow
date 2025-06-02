<template>
    <div class="student-view">
      <h2>Description</h2>
      <div class="description-container">
      <p>{{ description }}</p>
      </div>
      <iframe
        v-if="viewerUrl"
        :src="viewerUrl"
        class="iframe"
        frameborder="0"
      ></iframe>
  
      <button v-if="viewerUrl" @click="openInNewTab" class="button-blue">
        Open the viewer in a new tab
      </button>
  
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from "vue"
  import { useRoute } from "vue-router"
  
  const viewerUrl = ref("")
  const description = ref("")
  const error = ref("")
  const route = useRoute()
  
  async function validateToken(token) { // Function to validate the token and fetch the viewer URL
    try {
      const res = await fetch("http://localhost:5000/lti/validate_token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
        credentials: "include"
      })
  
      const data = await res.json()
      if (res.ok) {
        viewerUrl.value = data.viewer_url
        description.value = data.description
      } else {
        error.value = data.error || "Token validation error"
      }
    } catch {
      error.value = "Error during token validation"
    }
  }
  
  onMounted(() => {
    const token = route.query.token
    if (!token) {
      error.value = "Missing token in URL"
      return
    }
    validateToken(token)
  })
  
  function openInNewTab() { // Function to open the viewer URL in a new tab
    if (viewerUrl.value) {
      window.open(viewerUrl.value, "_blank")
    }
  }
  </script>