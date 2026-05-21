import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertOctagon, ArrowLeft, Check, MessageSquarePlus, X } from "lucide-react";

import {
  addDriverComment,
  approveEvent,
  dismissEvent,
  escalateEvent,
  finalizeCase,
  getCase,
  openProgressSocket,
} from "../api";
import { useAuth } from "../auth";
import { EventActionModal } from "../components/EventActionModal";
import { RiskMeter } from "../components/RiskMeter";
import { StatusBadge } from "../components/StatusBadge";
import type { DetectedEvent, SafetyCase } from "../types";

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.floor(seconds % 60);
  return `${minutes}:${remaining.toString().padStart(2, "0")}`;
}

export function CaseDetailPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [safetyCase, setSafetyCase] = useState<SafetyCase | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string | null>(null);
  const [modal, setModal] = useState<{ event: DetectedEvent; mode: "dismiss" | "escalate" } | null>(null);
  const [finalizing, setFinalizing] = useState(false);
  const [commentText, setCommentText] = useState("");

  const refresh = useCallback(async () => {
    if (!caseId) return;
    try {
      setSafetyCase(await getCase(caseId));
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load case");
    }
  }, [caseId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Stream progress while the backend processes the upload.
  useEffect(() => {
    if (!caseId || !safetyCase) return;
    if (safetyCase.status !== "processing" && safetyCase.status !== "new") return;
    const socket = openProgressSocket(caseId, (message) => {
      setProgressMessage(`${message.progress}% — ${message.message}`);
      if (message.status === "review" || message.status === "failed") {
        socket.close();
        refresh();
      }
    });
    return () => socket.close();
  }, [caseId, safetyCase?.status, refresh]);

  const pendingCount = useMemo(
    () => (safetyCase?.events ?? []).filter((event) => event.status === "pending").length,
    [safetyCase],
  );

  if (!caseId) return null;

  const canDecide = !!user && (user.role === "reviewer" || user.role === "manager");
  const isProcessing = safetyCase?.status === "processing" || safetyCase?.status === "new";

  async function handleDecision(event: DetectedEvent, kind: "approve" | "dismiss" | "escalate", text?: string) {
    if (!caseId) return;
    if (kind === "approve") await approveEvent(caseId, event.id);
    else if (kind === "dismiss") await dismissEvent(caseId, event.id, text ?? "");
    else await escalateEvent(caseId, event.id, text ?? "");
    await refresh();
  }

  async function handleFinalize() {
    if (!caseId) return;
    setFinalizing(true);
    try {
      await finalizeCase(caseId);
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not finalize");
    } finally {
      setFinalizing(false);
    }
  }

  async function handleAddComment() {
    if (!caseId || !safetyCase || !user?.driver_id || !commentText.trim()) return;
    await addDriverComment(safetyCase.driver_id, caseId, commentText.trim());
    setCommentText("");
    await refresh();
  }

  return (
    <div className="page">
      <header className="page-header">
        <button className="ghost-button" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Back
        </button>
        {safetyCase && (
          <div className="header-actions">
            <StatusBadge status={safetyCase.status} />
            {canDecide && safetyCase.status === "review" && pendingCount === 0 && (
              <button className="primary-button" onClick={handleFinalize} disabled={finalizing}>
                {finalizing ? "Finalizing…" : "Finalize case"}
              </button>
            )}
          </div>
        )}
      </header>

      {error && <div className="error-banner">{error}</div>}

      {!safetyCase && <p className="muted">Loading case…</p>}

      {safetyCase && (
        <>
          <section className="case-summary">
            <div>
              <p className="eyebrow">Driver</p>
              <h2>{safetyCase.driver?.name ?? "Unknown"}</h2>
              <p className="muted">
                {safetyCase.driver?.employee_id} · {safetyCase.driver?.vehicle_id ?? "no vehicle"}
              </p>
            </div>
            {safetyCase.driver && (
              <div className="case-summary-meter">
                <p className="eyebrow">Current risk score</p>
                <RiskMeter score={safetyCase.driver.risk_score} />
              </div>
            )}
            <div>
              <p className="eyebrow">Video</p>
              <p>{safetyCase.video_filename}</p>
              <p className="muted">
                Uploaded {new Date(safetyCase.created_at).toLocaleString()}
              </p>
            </div>
          </section>

          {isProcessing && (
            <section className="processing-banner">
              <strong>Processing video…</strong>
              <p>{progressMessage ?? `${safetyCase.progress}% — waiting for worker.`}</p>
            </section>
          )}

          {safetyCase.brief && (
            <section className="brief-card">
              <header>
                <p className="eyebrow">AI safety brief</p>
                <h2>{safetyCase.brief.verdict}</h2>
                <p className="muted">
                  Confidence {Math.round((safetyCase.brief.confidence ?? 0) * 100)}% · source{" "}
                  {safetyCase.brief.source ?? "heuristic"}
                </p>
              </header>
              <p>
                <strong>Recommended action:</strong> {safetyCase.brief.recommended_action}
              </p>
              {safetyCase.brief.evidence?.length > 0 && (
                <ul>
                  {safetyCase.brief.evidence.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              )}
            </section>
          )}

          <section>
            <header className="section-header">
              <h2>Evidence timeline</h2>
              {canDecide && pendingCount > 0 && (
                <span className="muted">
                  Decide on all {pendingCount} pending event(s) to enable Finalize.
                </span>
              )}
            </header>

            {safetyCase.events.length === 0 && (
              <p className="muted">No events yet — the analyzer is still scanning the clip.</p>
            )}

            <div className="event-list">
              {safetyCase.events.map((event) => (
                <article key={event.id} className={`event-row event-${event.severity}`}>
                  <div className="event-time">
                    <time>{formatTime(event.timestamp_seconds)}</time>
                    <span className="muted">{Math.round(event.confidence * 100)}% conf</span>
                  </div>
                  <div className="event-body">
                    <div className="event-title">
                      <strong>{event.event_type.replace(/_/g, " ")}</strong>
                      <StatusBadge status={event.status} />
                    </div>
                    <p>{event.description}</p>
                    {event.dismissal_reason && (
                      <p className="muted">
                        <strong>Dismissed:</strong> {event.dismissal_reason}
                      </p>
                    )}
                    {event.escalation_notes && (
                      <p className="muted">
                        <strong>Escalation note:</strong> {event.escalation_notes}
                      </p>
                    )}
                  </div>
                  {canDecide && (
                    <div className="event-actions">
                      <button
                        className="approve-button"
                        onClick={() => handleDecision(event, "approve")}
                        disabled={event.status === "approved"}
                        title="Confirm AI finding (+10 risk)"
                      >
                        <Check size={14} /> Approve
                      </button>
                      <button
                        className="dismiss-button"
                        onClick={() => setModal({ event, mode: "dismiss" })}
                        disabled={event.status === "dismissed"}
                        title="Mark as false positive"
                      >
                        <X size={14} /> Dismiss
                      </button>
                      <button
                        className="escalate-button"
                        onClick={() => setModal({ event, mode: "escalate" })}
                        disabled={event.status === "escalated"}
                        title="Send to manager (+25 risk)"
                      >
                        <AlertOctagon size={14} /> Escalate
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          </section>

          <section>
            <header className="section-header">
              <h2>Driver comments</h2>
            </header>
            {safetyCase.comments.length === 0 && (
              <p className="muted">No driver comments yet.</p>
            )}
            <ul className="comment-list">
              {safetyCase.comments.map((comment) => (
                <li key={comment.id}>
                  <p>{comment.text}</p>
                  <time className="muted">{new Date(comment.created_at).toLocaleString()}</time>
                </li>
              ))}
            </ul>

            {user?.role === "driver" && user.driver_id === safetyCase.driver_id && (
              <div className="comment-form">
                <textarea
                  rows={3}
                  placeholder="Add context the reviewer should see…"
                  value={commentText}
                  onChange={(event) => setCommentText(event.target.value)}
                />
                <button
                  className="primary-button"
                  onClick={handleAddComment}
                  disabled={!commentText.trim()}
                >
                  <MessageSquarePlus size={14} /> Post comment
                </button>
              </div>
            )}
          </section>
        </>
      )}

      <EventActionModal
        mode={modal?.mode ?? null}
        eventType={modal?.event.event_type ?? ""}
        onClose={() => setModal(null)}
        onSubmit={async (text) => {
          if (!modal) return;
          await handleDecision(modal.event, modal.mode, text);
        }}
      />
    </div>
  );
}
