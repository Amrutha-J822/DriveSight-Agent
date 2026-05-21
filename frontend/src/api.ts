import { getStoredUserId } from "./auth";
import type {
  Analytics,
  Coaching,
  DetectedEvent,
  Driver,
  DriverComment,
  ProgressMessage,
  SafetyCase,
  User,
} from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function withAuthHeaders(init: RequestInit = {}): RequestInit {
  const userId = getStoredUserId();
  const headers = new Headers(init.headers);
  if (userId) headers.set("X-User-Id", userId);
  return { ...init, headers };
}

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    let message = body;
    try {
      const parsed = JSON.parse(body);
      message = parsed.detail ?? body;
    } catch {
      // body wasn't JSON; use raw text
    }
    throw new Error(message || `Request failed with ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  return parse<T>(await fetch(`${API_BASE_URL}${path}`, withAuthHeaders()));
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const init: RequestInit = withAuthHeaders({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parse<T>(await fetch(`${API_BASE_URL}${path}`, init));
}

export const listUsersForLogin = () => get<User[]>("/api/users");
export const fetchMe = () => get<User>("/api/me");

export const listDrivers = () => get<Driver[]>("/api/drivers");
export const getDriver = (driverId: string) => get<Driver>(`/api/drivers/${driverId}`);
export const getDriverCases = (driverId: string) => get<SafetyCase[]>(`/api/drivers/${driverId}/cases`);
export const getDriverCoaching = (driverId: string) => get<Coaching[]>(`/api/drivers/${driverId}/coaching`);

export const acknowledgeCoaching = (driverId: string, recId: string) =>
  post<{ ok: boolean }>(`/api/drivers/${driverId}/coaching/${recId}/acknowledge`);

export const addDriverComment = (driverId: string, caseId: string, text: string) =>
  post<DriverComment>(`/api/drivers/${driverId}/cases/${caseId}/comment`, { text });

export const listCases = () => get<SafetyCase[]>("/api/cases");
export const getCase = (caseId: string) => get<SafetyCase>(`/api/cases/${caseId}`);

export async function uploadCase(driverId: string, file: File) {
  const formData = new FormData();
  formData.append("driver_id", driverId);
  formData.append("file", file);
  const response = await fetch(
    `${API_BASE_URL}/api/cases/upload`,
    withAuthHeaders({ method: "POST", body: formData }),
  );
  return parse<{ case_id: string; status: string }>(response);
}

export const approveEvent = (caseId: string, eventId: string) =>
  post<DetectedEvent>(`/api/cases/${caseId}/events/${eventId}/approve`);

export const dismissEvent = (caseId: string, eventId: string, reason: string) =>
  post<DetectedEvent>(`/api/cases/${caseId}/events/${eventId}/dismiss`, { reason });

export const escalateEvent = (caseId: string, eventId: string, notes: string) =>
  post<DetectedEvent>(`/api/cases/${caseId}/events/${eventId}/escalate`, { notes });

export const finalizeCase = (caseId: string, notes?: string) =>
  post<SafetyCase>(`/api/cases/${caseId}/finalize`, { notes });

export const closeEscalation = (caseId: string, resolutionNotes: string) =>
  post<SafetyCase>(`/api/cases/${caseId}/close-escalation`, { resolution_notes: resolutionNotes });

export const reprocessCase = (caseId: string) =>
  post<SafetyCase>(`/api/cases/${caseId}/reprocess`);

export const getAnalytics = () => get<Analytics>("/api/analytics");

// ----- Manager admin: drivers + users -----

async function patch<T>(path: string, body: unknown): Promise<T> {
  const init = withAuthHeaders({
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parse<T>(await fetch(`${API_BASE_URL}${path}`, init));
}

async function del<T = void>(path: string): Promise<T> {
  return parse<T>(await fetch(`${API_BASE_URL}${path}`, withAuthHeaders({ method: "DELETE" })));
}

export const createDriver = (body: { name: string; employee_id: string; vehicle_id?: string }) =>
  post<Driver>("/api/drivers", body);

export const updateDriver = (
  driverId: string,
  body: { name: string; employee_id: string; vehicle_id?: string },
) => patch<Driver>(`/api/drivers/${driverId}`, body);

export const deleteDriver = (driverId: string) => del(`/api/drivers/${driverId}`);

export const createUser = (body: {
  name: string;
  email: string;
  role: User["role"];
  driver_id?: string | null;
}) => post<User>("/api/users", body);

export const updateUser = (
  userId: string,
  body: { name: string; email: string; role: User["role"]; driver_id?: string | null },
) => patch<User>(`/api/users/${userId}`, body);

export const deleteUser = (userId: string) => del(`/api/users/${userId}`);

function websocketBaseUrl() {
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString().replace(/\/$/, "");
}

export function openProgressSocket(caseId: string, onMessage: (msg: ProgressMessage) => void) {
  const socket = new WebSocket(`${websocketBaseUrl()}/ws/progress/${caseId}`);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}
