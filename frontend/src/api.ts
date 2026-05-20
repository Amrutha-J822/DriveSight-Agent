import type { FeedbackAction, ProgressMessage, Report } from "./types";

const configuredApiUrl = import.meta.env.VITE_API_URL as string | undefined;
export const API_BASE_URL = configuredApiUrl ?? (import.meta.env.DEV ? "http://localhost:8000" : "");
const apiIsConfigured = Boolean(configuredApiUrl) || import.meta.env.DEV;

function requireApi() {
  if (!apiIsConfigured) {
    throw new Error(
      "This Vercel deployment is the frontend dashboard. Set VITE_API_URL to a hosted FastAPI backend to enable uploads and reports."
    );
  }
}

function websocketBaseUrl() {
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString().replace(/\/$/, "");
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadVideo(file: File) {
  requireApi();
  const formData = new FormData();
  formData.append("file", file);
  return parseResponse<{ report_id: string; status: string }>(
    await fetch(`${API_BASE_URL}/api/reports/upload`, {
      method: "POST",
      body: formData
    })
  );
}

export async function listReports() {
  if (!apiIsConfigured) return [];
  return parseResponse<Report[]>(await fetch(`${API_BASE_URL}/api/reports`));
}

export async function getReport(reportId: string) {
  requireApi();
  return parseResponse<Report>(await fetch(`${API_BASE_URL}/api/reports/${reportId}`));
}

export async function sendFeedback(reportId: string, action: FeedbackAction, note?: string) {
  requireApi();
  return parseResponse(
    await fetch(`${API_BASE_URL}/api/reports/${reportId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, note })
    })
  );
}

export function openProgressSocket(reportId: string, onMessage: (message: ProgressMessage) => void) {
  requireApi();
  const socket = new WebSocket(`${websocketBaseUrl()}/ws/progress/${reportId}`);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}
