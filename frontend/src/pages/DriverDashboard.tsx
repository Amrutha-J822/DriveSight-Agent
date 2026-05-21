import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";

import { acknowledgeCoaching, getDriver, getDriverCases, getDriverCoaching } from "../api";
import { RiskMeter } from "../components/RiskMeter";
import { StatusBadge } from "../components/StatusBadge";
import type { Coaching, Driver, SafetyCase } from "../types";

type Props = {
  driverId: string;
};

export function DriverDashboardPage({ driverId }: Props) {
  const [driver, setDriver] = useState<Driver | null>(null);
  const [cases, setCases] = useState<SafetyCase[]>([]);
  const [coaching, setCoaching] = useState<Coaching[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!driverId) return;
    try {
      const [d, c, k] = await Promise.all([
        getDriver(driverId),
        getDriverCases(driverId),
        getDriverCoaching(driverId),
      ]);
      setDriver(d);
      setCases(c);
      setCoaching(k);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load your dashboard");
    }
  }, [driverId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (!driverId) {
    return (
      <div className="page">
        <p className="muted">This account is not linked to a driver profile.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">My driver portal</p>
          <h1>{driver?.name ?? "…"}</h1>
          <p className="muted">
            {driver?.employee_id} · {driver?.vehicle_id ?? "no vehicle assigned"}
          </p>
        </div>
        {driver && (
          <div style={{ minWidth: 240 }}>
            <RiskMeter score={driver.risk_score} />
          </div>
        )}
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="stat-grid">
        <div className="stat-card">
          <strong>{driver?.total_events ?? 0}</strong>
          <p>Reviewed events</p>
        </div>
        <div className="stat-card">
          <strong>{driver?.approved_events ?? 0}</strong>
          <p>Confirmed risks</p>
        </div>
        <div className="stat-card">
          <strong>{driver?.escalated_events ?? 0}</strong>
          <p>Escalations</p>
        </div>
      </section>

      <section>
        <h2>Coaching recommendations</h2>
        {coaching.length === 0 && (
          <p className="muted">No coaching recommendations yet — keep up the safe driving.</p>
        )}
        <ul className="coaching-list">
          {coaching.map((rec) => (
            <li key={rec.id} className={rec.acknowledged ? "acknowledged" : ""}>
              <p>{rec.recommendation_text}</p>
              <footer>
                <time className="muted">{new Date(rec.created_at).toLocaleString()}</time>
                {rec.acknowledged ? (
                  <span className="muted">
                    <CheckCircle2 size={14} /> Acknowledged
                  </span>
                ) : (
                  <button
                    className="primary-button"
                    onClick={async () => {
                      await acknowledgeCoaching(driverId, rec.id);
                      await refresh();
                    }}
                  >
                    Acknowledge
                  </button>
                )}
              </footer>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>My case history</h2>
        {cases.length === 0 && <p className="muted">No cases yet.</p>}
        <div className="case-grid">
          {cases.map((safetyCase) => (
            <Link key={safetyCase.id} to={`/cases/${safetyCase.id}`} className="case-card">
              <div className="case-card-top">
                <strong>{safetyCase.video_filename}</strong>
                <StatusBadge status={safetyCase.status} />
              </div>
              <p className="muted">{safetyCase.events.length} event(s)</p>
              <div className="case-card-bottom">
                <time>{new Date(safetyCase.created_at).toLocaleString()}</time>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
