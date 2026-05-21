export type Role = "driver" | "reviewer" | "manager";

export type User = {
  id: string;
  name: string;
  email: string;
  role: Role;
  driver_id: string | null;
  created_at: string;
};

export type Driver = {
  id: string;
  name: string;
  employee_id: string;
  vehicle_id: string | null;
  risk_score: number;
  total_events: number;
  approved_events: number;
  dismissed_events: number;
  escalated_events: number;
  created_at: string;
};

export type EventStatus = "pending" | "approved" | "dismissed" | "escalated";

export type DetectedEvent = {
  id: string;
  case_id: string;
  event_type: string;
  timestamp_seconds: number;
  severity: "info" | "low" | "medium" | "high" | "critical";
  confidence: number;
  description: string;
  evidence: Record<string, unknown>;
  status: EventStatus;
  dismissal_reason: string | null;
  escalation_notes: string | null;
  reviewer_id: string | null;
  reviewed_at: string | null;
  created_at: string;
};

export type DrivingRiskBrief = {
  verdict: string;
  confidence: number;
  evidence: string[];
  recommended_action: string;
  key_questions: string[];
  source?: string;
};

export type DriverComment = {
  id: number;
  case_id: string;
  driver_id: string;
  text: string;
  created_at: string;
};

export type CaseStatus =
  | "new"
  | "processing"
  | "review"
  | "approved"
  | "dismissed"
  | "escalated"
  | "resolved"
  | "failed";

export type SafetyCase = {
  id: string;
  driver_id: string;
  reviewer_id: string | null;
  video_filename: string;
  status: CaseStatus;
  progress: number;
  ai_summary: string | null;
  brief: DrivingRiskBrief | null;
  reviewer_notes: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
  events: DetectedEvent[];
  driver: Driver | null;
  comments: DriverComment[];
};

export type Coaching = {
  id: string;
  driver_id: string;
  case_id: string | null;
  recommendation_text: string;
  reason: string;
  acknowledged: boolean;
  acknowledged_at: string | null;
  created_at: string;
};

export type ProgressMessage = {
  case_id: string;
  status: CaseStatus;
  progress: number;
  message: string;
};

export type Analytics = {
  total_cases: number;
  reviewed_cases: number;
  pending_escalations: number;
  false_positive_rate: number;
  most_common_event: string | null;
  high_risk_drivers: Array<{ id: string; name: string; risk_score: number }>;
};
