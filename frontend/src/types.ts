export type FeedbackAction = "approve" | "dismiss" | "escalate";

export type Feedback = {
  id: number;
  report_id: string;
  action: FeedbackAction;
  note: string | null;
  created_at: string;
};

export type RiskEvent = {
  type: string;
  timestamp_seconds: number;
  severity: "info" | "medium" | "high";
  description: string;
  evidence: Record<string, unknown>;
};

export type DrivingRiskBrief = {
  verdict: string;
  confidence: number;
  evidence: string[];
  recommended_action: string;
  key_questions: string[];
  source?: string;
};

export type Report = {
  id: string;
  filename: string;
  status: "queued" | "processing" | "summarizing" | "complete" | "failed";
  progress: number;
  verdict: string | null;
  confidence: number | null;
  brief: DrivingRiskBrief | null;
  events: RiskEvent[];
  feedback: Feedback[];
  error: string | null;
  created_at: string;
  updated_at: string;
};

export type ProgressMessage = {
  report_id: string;
  status: Report["status"];
  progress: number;
  message: string;
};
