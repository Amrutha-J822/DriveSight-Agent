import { ChangeEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud } from "lucide-react";

import { listDrivers, uploadCase } from "../api";
import type { Driver } from "../types";

export function UploadCasePage() {
  const navigate = useNavigate();
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [driverId, setDriverId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDrivers()
      .then((d) => {
        setDrivers(d);
        setDriverId(d[0]?.id ?? "");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load drivers"));
  }, []);

  async function handleSubmit() {
    if (!driverId || !file) {
      setError("Pick a driver and a video file.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const { case_id } = await uploadCase(driverId, file);
      navigate(`/cases/${case_id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed");
    } finally {
      setSubmitting(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Reviewer</p>
          <h1>New safety review case</h1>
          <p className="muted">
            Pick a driver and upload their dashcam clip. The case will appear in the queue with AI-detected
            events ready for your decision.
          </p>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="upload-form">
        <label>
          <span>Driver</span>
          <select value={driverId} onChange={(event) => setDriverId(event.target.value)}>
            {drivers.map((driver) => (
              <option key={driver.id} value={driver.id}>
                {driver.name} · {driver.employee_id} (risk {driver.risk_score})
              </option>
            ))}
          </select>
        </label>

        <label className="file-drop">
          <UploadCloud size={28} />
          <span>{file ? file.name : "Choose dashcam video"}</span>
          <input type="file" accept="video/*" onChange={handleFileChange} />
        </label>

        <button className="primary-button" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Uploading…" : "Create case"}
        </button>
      </section>
    </div>
  );
}
