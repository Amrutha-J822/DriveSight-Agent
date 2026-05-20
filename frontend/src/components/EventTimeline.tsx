import type { RiskEvent } from "../types";

type Props = {
  events: RiskEvent[];
};

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

export function EventTimeline({ events }: Props) {
  return (
    <section className="timeline">
      <h3>Event timeline</h3>
      {events.length === 0 && <p className="muted">Events will appear after processing completes.</p>}
      {events.map((event, index) => (
        <article className={`timeline-item ${event.severity}`} key={`${event.type}-${event.timestamp_seconds}-${index}`}>
          <time>{formatTime(event.timestamp_seconds)}</time>
          <div>
            <span>{event.type.replace(/_/g, " ")}</span>
            <p>{event.description}</p>
          </div>
        </article>
      ))}
    </section>
  );
}
