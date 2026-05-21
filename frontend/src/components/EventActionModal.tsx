import { useEffect, useState } from "react";

type Props = {
  mode: "dismiss" | "escalate" | null;
  eventType: string;
  onClose: () => void;
  onSubmit: (text: string) => Promise<void>;
};

export function EventActionModal({ mode, eventType, onClose, onSubmit }: Props) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setText("");
    setError(null);
  }, [mode, eventType]);

  if (!mode) return null;

  const isDismiss = mode === "dismiss";
  const title = isDismiss ? "Dismiss event" : "Escalate event";
  const label = isDismiss ? "Why is this a false positive?" : "Why does this need escalation?";
  const placeholder = isDismiss
    ? "e.g. Pedestrian was on sidewalk, not in vehicle path"
    : "e.g. Driver has 3 lane-drift events this week; manager review required";

  async function handleSubmit() {
    if (!text.trim()) {
      setError("A short note is required.");
      return;
    }
    setSubmitting(true);
    try {
      await onSubmit(text.trim());
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Action failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <header>
          <h3>{title}</h3>
          <p className="muted">Event: {eventType.replace(/_/g, " ")}</p>
        </header>
        <label>
          <span>{label}</span>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder={placeholder}
            rows={4}
            autoFocus
          />
        </label>
        {error && <p className="error-banner inline">{error}</p>}
        <footer>
          <button className="ghost-button" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button
            className={isDismiss ? "dismiss-button" : "escalate-button"}
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Saving…" : isDismiss ? "Dismiss" : "Escalate"}
          </button>
        </footer>
      </div>
    </div>
  );
}
