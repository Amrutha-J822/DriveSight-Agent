import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw } from "lucide-react";

import { listCases } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import type { SafetyCase } from "../types";

const REVIEWABLE: SafetyCase["status"][] = ["new", "processing", "review"];

export function ReviewerDashboardPage() {
  const [cases, setCases] = useState<SafetyCase[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setCases(await listCases());
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load cases");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const pending = cases.filter((c) => REVIEWABLE.includes(c.status));
  const decided = cases.filter((c) => !REVIEWABLE.includes(c.status));

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Reviewer portal</p>
          <h1>Case queue</h1>
        </div>
        <div className="header-actions">
          <Link to="/upload" className="primary-button">
            Upload new case
          </Link>
          <button className="ghost-button" onClick={refresh}>
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section>
        <h2>Pending review ({pending.length})</h2>
        {pending.length === 0 && (
          <p className="muted">No cases waiting. Upload a dashcam video to create a new case.</p>
        )}
        <div className="case-grid">
          {pending.map((safetyCase) => (
            <CaseCard key={safetyCase.id} safetyCase={safetyCase} />
          ))}
        </div>
      </section>

      <section>
        <h2>Decided ({decided.length})</h2>
        <div className="case-grid">
          {decided.map((safetyCase) => (
            <CaseCard key={safetyCase.id} safetyCase={safetyCase} />
          ))}
        </div>
      </section>
    </div>
  );
}

function CaseCard({ safetyCase }: { safetyCase: SafetyCase }) {
  const pendingEvents = safetyCase.events.filter((event) => event.status === "pending").length;
  return (
    <Link to={`/cases/${safetyCase.id}`} className="case-card">
      <div className="case-card-top">
        <strong>{safetyCase.driver?.name ?? "Unknown driver"}</strong>
        <StatusBadge status={safetyCase.status} />
      </div>
      <p className="muted">{safetyCase.video_filename}</p>
      <div className="case-card-bottom">
        <span>{safetyCase.events.length} event(s)</span>
        {pendingEvents > 0 && <span className="pill">{pendingEvents} pending</span>}
        <time>{new Date(safetyCase.created_at).toLocaleString()}</time>
      </div>
    </Link>
  );
}
