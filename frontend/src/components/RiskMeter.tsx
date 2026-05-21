type Props = {
  score: number;
};

export function RiskMeter({ score }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  const tier = clamped >= 75 ? "high" : clamped >= 50 ? "medium" : "low";
  const label = tier === "high" ? "High risk" : tier === "medium" ? "Watch list" : "Low risk";

  return (
    <div className={`risk-meter risk-${tier}`}>
      <div className="risk-meter-header">
        <strong>{clamped}</strong>
        <span>/ 100</span>
        <em>{label}</em>
      </div>
      <div className="risk-meter-track">
        <div style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
