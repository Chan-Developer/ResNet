<template>
  <el-container class="app-container">
    <AppSidebar v-if="userStore.token" />
    <el-main class="main-area">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import AppSidebar from './components/AppSidebar.vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
  --pink: #d7a1ad;
  --pink-light: #f8e9ed;
  --pink-deep: #b26a7f;
  --green: #9dbfb6;
  --green-light: #eaf3f1;
  --green-deep: #4f7f75;
  --lavender: #cbb8c6;
  --lavender-light: #f2ecf1;
  --sky: #a7c7e7;
  --sky-light: #edf4fb;
  --peach: #f2c7b2;
  --peach-light: #fff2ea;
  --bg: #faf7f8;
  --card-bg: rgba(255, 255, 255, 0.82);
  --card-border: rgba(220, 210, 218, 0.6);
  --text-primary: #3f2f36;
  --text-secondary: #6f5e66;
  --text-muted: #a1949a;
  --radius-sm: 12px;
  --radius-md: 18px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --shadow-soft: 0 8px 24px rgba(88, 70, 80, 0.08);
  --shadow-hover: 0 12px 32px rgba(88, 70, 80, 0.14);
  --glass-blur: blur(18px);
  --font-body: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-display: 'Playfair Display', 'PingFang SC', 'Microsoft YaHei', serif;
}

html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: var(--font-body);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3 {
  font-family: var(--font-display);
  letter-spacing: 0.2px;
}

.app-container {
  height: 100vh;
}

.main-area {
  background:
    radial-gradient(ellipse at 20% 0%, rgba(215, 161, 173, 0.14) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 100%, rgba(157, 191, 182, 0.12) 0%, transparent 55%),
    radial-gradient(ellipse at 50% 50%, rgba(167, 199, 231, 0.08) 0%, transparent 60%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0)),
    var(--bg);
  overflow-y: auto;
}

/* ---- Element Plus overrides ---- */
.el-button--primary {
  --el-button-bg-color: var(--pink-deep);
  --el-button-border-color: var(--pink-deep);
  --el-button-hover-bg-color: #a9576d;
  --el-button-hover-border-color: #a9576d;
  --el-button-active-bg-color: #8d4356;
  --el-button-active-border-color: #8d4356;
  border-radius: var(--radius-sm) !important;
  font-weight: 700;
}

.el-card {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--card-border) !important;
  background: var(--card-bg) !important;
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--shadow-soft) !important;
  transition: box-shadow 0.3s, transform 0.3s !important;
}
.el-card:hover {
  box-shadow: var(--shadow-hover) !important;
}

.el-input__wrapper {
  border-radius: var(--radius-sm) !important;
  box-shadow: 0 0 0 1px #e7d8e0 inset !important;
  transition: box-shadow 0.2s;
}
.el-input__wrapper:hover,
.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1.5px var(--pink) inset !important;
}

.el-table {
  --el-table-border-color: #f2e8ee;
  --el-table-header-bg-color: var(--lavender-light);
  --el-table-row-hover-bg-color: #fbf1f5;
  border-radius: var(--radius-md) !important;
  overflow: hidden;
}
.el-table th.el-table__cell {
  color: var(--text-primary) !important;
  font-weight: 700;
}

.el-pagination {
  --el-pagination-button-bg-color: var(--pink-light);
  --el-pagination-hover-color: var(--pink-deep);
}
.el-pagination .is-active {
  background: var(--pink-deep) !important;
  color: #fff !important;
  border-radius: 10px;
}

.el-tabs__item.is-active {
  color: var(--pink-deep) !important;
}
.el-tabs__active-bar {
  background-color: var(--pink-deep) !important;
}

.el-menu-item.is-active {
  color: var(--pink-deep) !important;
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light)) !important;
}

.el-radio-button__inner {
  border-radius: var(--radius-sm) !important;
}
.el-radio-button:first-child .el-radio-button__inner {
  border-radius: var(--radius-sm) 0 0 var(--radius-sm) !important;
}
.el-radio-button:last-child .el-radio-button__inner {
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0 !important;
}

.el-upload--picture-card {
  border-radius: var(--radius-md) !important;
  border: 2px dashed var(--lavender) !important;
  background: var(--lavender-light) !important;
  transition: border-color 0.3s, background 0.3s;
}
.el-upload--picture-card:hover {
  border-color: var(--pink) !important;
  background: var(--pink-light) !important;
}
.el-upload-list--picture-card .el-upload-list__item {
  border-radius: var(--radius-md) !important;
  border: 2px solid var(--card-border) !important;
}

.el-progress-bar__outer {
  border-radius: 20px !important;
}
.el-progress-bar__inner {
  border-radius: 20px !important;
}

.el-page-header__back {
  color: var(--text-primary);
}

/* ---- Page transition ---- */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ---- Scrollbar ---- */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--lavender);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--pink);
}
</style>
