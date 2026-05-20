import { AlertOctagon, Check, X } from "lucide-react";

import type { FeedbackAction } from "../types";

type Props = {
  disabled: boolean;
  onFeedback: (action: FeedbackAction) => void;
};

export function FeedbackButtons({ disabled, onFeedback }: Props) {
  return (
    <div className="feedback-buttons">
      <button disabled={disabled} onClick={() => onFeedback("approve")} title="Approve report">
        <Check size={16} />
        Approve
      </button>
      <button disabled={disabled} onClick={() => onFeedback("dismiss")} title="Dismiss report">
        <X size={16} />
        Dismiss
      </button>
      <button disabled={disabled} onClick={() => onFeedback("escalate")} title="Escalate report">
        <AlertOctagon size={16} />
        Escalate
      </button>
    </div>
  );
}
