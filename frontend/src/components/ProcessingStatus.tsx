import type { ProgressMessage } from "../types";

type Props = {
  progress: ProgressMessage | null;
};

export function ProcessingStatus({ progress }: Props) {
  const percent = progress?.progress ?? 0;

  return (
    <section className="progress-panel">
      <div>
        <h2>Processing</h2>
        <span>{percent}%</span>
      </div>
      <div className="progress-track">
        <div style={{ width: `${percent}%` }} />
      </div>
      <p>{progress?.message ?? "Waiting for a new upload."}</p>
    </section>
  );
}
