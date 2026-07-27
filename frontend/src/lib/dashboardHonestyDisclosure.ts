/**
 * Progressive disclosure for Dashboard honesty chrome.
 * Labels (ACTUAL/PROXY/DERIVAT) stay available; only verbose gap/banner noise collapses.
 */

const BANNER_KEY = "workos-dashboard-honesty-banner-ack-v1";
const GAPS_KEY = "workos-dashboard-honesty-gaps-ack-v1";

function readBool(key: string): boolean {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

function writeBool(key: string, value: boolean): void {
  try {
    if (value) localStorage.setItem(key, "1");
    else localStorage.removeItem(key);
  } catch {
    // localStorage unavailable — keep in-memory only
  }
}

export function readDashboardBannerAcknowledged(): boolean {
  return readBool(BANNER_KEY);
}

export function writeDashboardBannerAcknowledged(value: boolean): void {
  writeBool(BANNER_KEY, value);
}

export function readDashboardGapsAcknowledged(): boolean {
  return readBool(GAPS_KEY);
}

export function writeDashboardGapsAcknowledged(value: boolean): void {
  writeBool(GAPS_KEY, value);
}
