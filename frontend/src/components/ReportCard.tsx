import { AlertTriangle, CheckCircle2, Clock3 } from "lucide-react";

import type { Report } from "../types";

type Props = {
  report: Report;
  isSelected: boolean;
  onSelect: () => void;
};

export function ReportCard({ report, isSelected, onSelect }: Props) {
  const Icon = report.status === "complete" ? CheckCircle2 : report.status === "failed" ? AlertTriangle : Clock3;

  return (
    <button className={`report-card ${isSelected ? "selected" : ""}`} onClick={onSelect}>
      <Icon size={18} />
      <span>
        <strong>{report.filename}</strong>
        <small>
          {report.verdict ?? report.status} · {new Date(report.created_at).toLocaleString()}
        </small>
      </span>
    </button>
  );
}
