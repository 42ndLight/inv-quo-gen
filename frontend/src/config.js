// Centralized API configuration (Method 1: Vite Build-Time Environment Variables)
//
// In local development: reads from frontend/.env or defaults to "/api" (proxied by Vite dev server).
// In Vercel production: reads from VITE_API_URL set in the Vercel project environment variables
// (e.g., https://your-railway-app.up.railway.app/api).

export const API_URL = import.meta.env.VITE_API_URL || "/api";

export default {
  API_URL,
};

