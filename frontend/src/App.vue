<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-800 font-sans antialiased">
    <!-- Header Navbar -->
    <header class="bg-indigo-700 text-white shadow-md sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-3">
            <svg class="h-8 w-8 text-indigo-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span class="text-xl font-bold tracking-tight">EquipHire</span>
            <span class="text-xs bg-indigo-500 px-2 py-0.5 rounded-full text-indigo-100 font-semibold uppercase tracking-wide">
              Manager
            </span>
          </div>
          <div class="flex items-center space-x-4">
            <router-link to="/" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-600 transition duration-150">
              Dashboard & Editor
            </router-link>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <RouterView />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 mt-12 py-6 text-center text-xs text-slate-500">
      <div class="max-w-7xl mx-auto px-4">
        &copy; 2026 EquipHire Document Manager. All rights reserved.
      </div>
    </footer>
  </div>
</template>

<style>
/* Remove default margins/padding that index.html/app wrapper might have if they interfere */
body {
  margin: 0;
}
</style>
