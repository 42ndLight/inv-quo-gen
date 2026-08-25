// Centralized runtime/build-time configuration.
// Resolution order:
//   1. window.config.API_URL — injected via public/config.js, can be
//      regenerated at deploy time without rebuilding the app (prod-friendly).
//   2. import.meta.env.VITE_API_URL — Vite build-time env var (.env files).
//   3. "/api" fallback for local dev (proxied by Vite dev server).
const runtimeConfig = typeof window !== "undefined" ? window.config : undefined;

export const API_URL =
  runtimeConfig?.API_URL || import.meta.env.VITE_API_URL || "/api";

export default {
  API_URL,
};
