import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { getAPIBaseURL, loadRuntimeConfig } from './lib/config.ts';
import { installCsrfFetchHeaderSupport } from './lib/csrf.ts';
import {
  installLocalApiWriteGuard,
  probeLocalApiCompatibility,
} from './lib/localApiCompatibility.ts';

// Load runtime configuration before rendering the app
async function initializeApp() {
  installCsrfFetchHeaderSupport();
  installLocalApiWriteGuard();

  try {
    await loadRuntimeConfig();
    if (import.meta.env.DEV) {
      const apiBase = getAPIBaseURL();
      console.info(
        `[WorkOS local] API base = ${apiBase || '(same-origin / Vite proxy)'}`,
      );
      const compat = await probeLocalApiCompatibility({ apiBase });
      if (compat.kind !== 'ok') {
        console.warn(`[WorkOS local] ${compat.kind}: ${compat.detail}`);
      }
    } else {
      console.log('Runtime configuration loaded successfully');
    }
  } catch (error) {
    console.warn(
      'Failed to load runtime configuration, using defaults:',
      error
    );
  }

  // Render the app
  createRoot(document.getElementById('root')!).render(<App />);
}

// Initialize the app
initializeApp();
