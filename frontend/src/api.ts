import type { FeedbackAction, ProgressMessage, Report } from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

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
  return parseResponse<Report[]>(await fetch(`${API_BASE_URL}/api/reports`));
}

export async function getReport(reportId: string) {
  return parseResponse<Report>(await fetch(`${API_BASE_URL}/api/reports/${reportId}`));
}

export async function sendFeedback(reportId: string, action: FeedbackAction, note?: string) {
  return parseResponse(
    await fetch(`${API_BASE_URL}/api/reports/${reportId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, note })
    })
  );
}

export function openProgressSocket(reportId: string, onMessage: (message: ProgressMessage) => void) {
  const socket = new WebSocket(`${websocketBaseUrl()}/ws/progress/${reportId}`);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}
