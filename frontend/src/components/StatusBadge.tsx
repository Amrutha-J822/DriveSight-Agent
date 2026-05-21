import type { CaseStatus, EventStatus } from "../types";

const LABELS: Record<string, string> = {
  new: "New",
  processing: "Processing",
  review: "Awaiting review",
  approved: "Approved",
  dismissed: "Dismissed",
  escalated: "Escalated",
  failed: "Failed",
  pending: "Pending",
};

export function StatusBadge({ status }: { status: CaseStatus | EventStatus }) {
  return <span className={`badge badge-${status}`}>{LABELS[status] ?? status}</span>;
}
