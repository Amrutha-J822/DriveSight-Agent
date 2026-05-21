import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listCases } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import type { SafetyCase } from "../types";

export function EscalationsPage() {
  const [cases, setCases] = useState<SafetyCase[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCases()
      .then((all) => setCases(all.filter((c) => c.status === "escalated")))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load escalations"));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Manager · escalations</p>
          <h1>Escalation queue</h1>
          <p className="muted">
            Cases reviewers flagged for manager attention. Open one and click <strong>Close escalation</strong>{" "}
            to mark it resolved with notes the driver will see.
          </p>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {cases.length === 0 && <p className="muted">No escalated cases. Nice.</p>}

      <div className="case-grid">
        {cases.map((safetyCase) => {
          const escalated = safetyCase.events.filter((event) => event.status === "escalated");
          return (
            <Link key={safetyCase.id} to={`/cases/${safetyCase.id}`} className="case-card">
              <div className="case-card-top">
                <strong>{safetyCase.driver?.name ?? "Unknown driver"}</strong>
                <StatusBadge status={safetyCase.status} />
              </div>
              <p className="muted">{safetyCase.video_filename}</p>
              <ul className="muted" style={{ paddingLeft: 18, margin: 0 }}>
                {escalated.slice(0, 3).map((event) => (
                  <li key={event.id}>
                    {event.event_type.replace(/_/g, " ")} —{" "}
                    {(event.escalation_notes ?? "").slice(0, 60)}
                  </li>
                ))}
              </ul>
              <div className="case-card-bottom">
                <time>{new Date(safetyCase.updated_at).toLocaleString()}</time>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
