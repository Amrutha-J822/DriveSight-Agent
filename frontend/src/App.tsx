import { useEffect, useMemo, useState } from "react";
import { Activity, ClipboardList, RefreshCw, ShieldAlert } from "lucide-react";

import { getReport, listReports, openProgressSocket, sendFeedback, uploadVideo } from "./api";
import { EventTimeline } from "./components/EventTimeline";
import { FeedbackButtons } from "./components/FeedbackButtons";
import { ProcessingStatus } from "./components/ProcessingStatus";
import { ReportCard } from "./components/ReportCard";
import { UploadPanel } from "./components/UploadPanel";
import type { FeedbackAction, ProgressMessage, Report } from "./types";

export default function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressMessage | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedReport = useMemo(
    () => reports.find((report) => report.id === selectedReportId) ?? reports[0] ?? null,
    [reports, selectedReportId]
  );

  async function refreshReports(nextSelectedId?: string) {
    const data = await listReports();
    setReports(data);
    if (nextSelectedId) {
      setSelectedReportId(nextSelectedId);
    } else if (!selectedReportId && data[0]) {
      setSelectedReportId(data[0].id);
    }
  }

  useEffect(() => {
    refreshReports().catch((caught) => setError(caught.message));
  }, []);

  async function handleUpload(file: File) {
    setError(null);
    setIsUploading(true);
    try {
      const upload = await uploadVideo(file);
      setSelectedReportId(upload.report_id);
      setProgress({
        report_id: upload.report_id,
        status: "queued",
        progress: 0,
        message: "Upload complete. Waiting for processing to start."
      });

      const socket = openProgressSocket(upload.report_id, async (message) => {
        setProgress(message);
        if (message.status === "complete" || message.status === "failed") {
          socket.close();
          const report = await getReport(upload.report_id);
          setReports((current) => [report, ...current.filter((item) => item.id !== report.id)]);
        }
      });

      await refreshReports(upload.report_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleFeedback(action: FeedbackAction) {
    if (!selectedReport) return;
    await sendFeedback(selectedReport.id, action);
    await refreshReports(selectedReport.id);
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Dashcam risk review</p>
          <h1>DriveSight Agent</h1>
        </div>
        <button className="ghost-button" onClick={() => refreshReports()} title="Refresh reports">
          <RefreshCw size={18} />
          Refresh
        </button>
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="summary-grid">
        <div className="metric">
          <ClipboardList size={22} />
          <span>{reports.length}</span>
          <p>Total reports</p>
        </div>
        <div className="metric">
          <ShieldAlert size={22} />
          <span>{reports.filter((report) => report.verdict?.includes("Elevated")).length}</span>
          <p>Elevated risk</p>
        </div>
        <div className="metric">
          <Activity size={22} />
          <span>{reports.reduce((total, report) => total + report.events.length, 0)}</span>
          <p>Events logged</p>
        </div>
      </section>

      <section className="workspace-grid">
        <aside className="left-panel">
          <UploadPanel onUpload={handleUpload} isUploading={isUploading} />
          <ProcessingStatus progress={progress} />
          <div className="report-list">
            <h2>Reports</h2>
            {reports.length === 0 && <p className="muted">Upload a dashcam video to create the first report.</p>}
            {reports.map((report) => (
              <ReportCard
                key={report.id}
                report={report}
                isSelected={selectedReport?.id === report.id}
                onSelect={() => setSelectedReportId(report.id)}
              />
            ))}
          </div>
        </aside>

        <section className="detail-panel">
          {selectedReport ? (
            <>
              <div className="brief-header">
                <div>
                  <p className="eyebrow">Driving Risk Brief</p>
                  <h2>{selectedReport.brief?.verdict ?? selectedReport.status}</h2>
                </div>
                <FeedbackButtons disabled={selectedReport.status !== "complete"} onFeedback={handleFeedback} />
              </div>

              {selectedReport.error && <div className="error-banner">{selectedReport.error}</div>}

              <div className="brief-grid">
                <article>
                  <h3>Confidence</h3>
                  <strong>{Math.round((selectedReport.brief?.confidence ?? 0) * 100)}%</strong>
                  <p className="muted">Source: {selectedReport.brief?.source ?? "pending"}</p>
                </article>
                <article>
                  <h3>Recommended action</h3>
                  <p>{selectedReport.brief?.recommended_action ?? "Processing has not produced a brief yet."}</p>
                </article>
              </div>

              <section className="evidence-section">
                <h3>Evidence</h3>
                <ul>
                  {(selectedReport.brief?.evidence ?? ["Waiting for analysis."]).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>

              <section className="evidence-section">
                <h3>Key questions</h3>
                <ul>
                  {(selectedReport.brief?.key_questions ?? ["What context should reviewers verify?"]).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>

              <EventTimeline events={selectedReport.events} />

              <section className="feedback-log">
                <h3>Feedback history</h3>
                {selectedReport.feedback.length === 0 && <p className="muted">No feedback yet.</p>}
                {selectedReport.feedback.map((item) => (
                  <p key={item.id}>
                    <strong>{item.action}</strong> on {new Date(item.created_at).toLocaleString()}
                  </p>
                ))}
              </section>
            </>
          ) : (
            <div className="empty-state">
              <h2>No report selected</h2>
              <p>Upload a video or select a previous report to inspect the risk brief.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
