import { createRouter, createWebHistory } from "vue-router";
import StudyList from "@/components/StudyList.vue";
import StudentView from "@/components/Student.vue";

const routes = [
    { path: "/", name: "StudyList", component: StudyList }, 
    { path: "/student", name: "Student", component: StudentView }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

export default router;
