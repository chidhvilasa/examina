import { cn } from "@/lib/utils";

interface ConfidenceBarProps {
  value: number;
  colorOverride?: string;
  className?: string;
}

export function confidenceColor(value: number): string {
  if (value >= 0.7) return "var(--confidence-high)";
  if (value >= 0.45) return "var(--confidence-medium)";
  return "var(--confidence-low)";
}

export function ConfidenceBar({ value, colorOverride, className }: ConfidenceBarProps) {
  const widthPercent = value >= 1 ? 100 : Math.max(0, value) * 100;
  const color = colorOverride ?? confidenceColor(value);

  return (
    <div
      className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)}
      role="progressbar"
      aria-valuenow={Math.round(value * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${widthPercent}%`, backgroundColor: color }}
      />
    </div>
  );
}
