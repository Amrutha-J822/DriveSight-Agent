import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getAnalytics, listDrivers } from "../api";
import { RiskMeter } from "../components/RiskMeter";
import type { Analytics, Driver } from "../types";

export function ManagerDashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getAnalytics(), listDrivers()])
      .then(([a, d]) => {
        setAnalytics(a);
        setDrivers(d);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load analytics"));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Manager portal</p>
          <h1>Fleet safety overview</h1>
        </div>
        <Link to="/queue" className="ghost-button">
          Open case queue →
        </Link>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {analytics && (
        <section className="stat-grid">
          <div className="stat-card">
            <strong>{analytics.total_cases}</strong>
            <p>Total cases</p>
          </div>
          <div className="stat-card">
            <strong>{analytics.reviewed_cases}</strong>
            <p>Reviewed</p>
          </div>
          <div className="stat-card">
            <strong>{analytics.pending_escalations}</strong>
            <p>Pending escalations</p>
          </div>
          <div className="stat-card">
            <strong>{Math.round(analytics.false_positive_rate * 100)}%</strong>
            <p>AI false-positive rate</p>
          </div>
          <div className="stat-card wide">
            <strong>{analytics.most_common_event?.replace(/_/g, " ") ?? "—"}</strong>
            <p>Most common approved risk type</p>
          </div>
        </section>
      )}

      <section>
        <h2>High-risk drivers</h2>
        {analytics?.high_risk_drivers.length === 0 && (
          <p className="muted">No drivers above 70 risk score yet.</p>
        )}
        <div className="driver-grid">
          {analytics?.high_risk_drivers.map((driver) => (
            <article key={driver.id} className="driver-card">
              <strong>{driver.name}</strong>
              <RiskMeter score={driver.risk_score} />
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>All drivers</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Driver</th>
              <th>Employee</th>
              <th>Vehicle</th>
              <th>Risk</th>
              <th>Approved</th>
              <th>Dismissed</th>
              <th>Escalated</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((driver) => (
              <tr key={driver.id}>
                <td>{driver.name}</td>
                <td>{driver.employee_id}</td>
                <td>{driver.vehicle_id ?? "—"}</td>
                <td>
                  <strong className={driver.risk_score >= 70 ? "risk-text-high" : ""}>
                    {driver.risk_score}
                  </strong>
                </td>
                <td>{driver.approved_events}</td>
                <td>{driver.dismissed_events}</td>
                <td>{driver.escalated_events}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
