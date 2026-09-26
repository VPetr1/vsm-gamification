import { signed } from "../utils/time";

type Props = {
  label: string;
  value: number;
  kind: "loyalty" | "safety";
  delta?: number | null;
  animateKey?: number;
};

export function ScaleBar({ label, value, kind, delta, animateKey }: Props) {
  const level = value < 30 ? "critical" : value < 50 ? "warn" : "ok";
  return (
    <div className={`scale scale-${kind} scale-${level}`}>
      <div className="scale-head">
        <span className="scale-label">{label}</span>
        <span className="scale-value">
          {value}
          {delta ? (
            <span key={animateKey} className={`delta ${delta > 0 ? "delta-up" : "delta-down"}`}>
              {signed(delta)}
            </span>
          ) : null}
        </span>
      </div>
      <div
        className="scale-track"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
      >
        <div className="scale-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
