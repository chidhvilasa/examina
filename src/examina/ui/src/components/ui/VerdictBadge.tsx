import type { VerdictType } from "@/lib/types";
import { cn } from "@/lib/utils";

const VERDICT_DISPLAY: Record<VerdictType, string> = {
  LIKELY_AUTHENTIC: "Likely Authentic",
  LIKELY_MANIPULATED: "Likely Manipulated",
  LIKELY_AI_GENERATED: "Likely AI-Generated",
  AI_ASSISTED: "AI-Assisted",
  INSUFFICIENT_EVIDENCE: "Insufficient Evidence",
  MIXED_SIGNALS: "Mixed Signals",
};

const VERDICT_COLOR_VAR: Record<VerdictType, string> = {
  LIKELY_AUTHENTIC: "var(--verdict-authentic)",
  LIKELY_MANIPULATED: "var(--verdict-manipulated)",
  LIKELY_AI_GENERATED: "var(--verdict-ai-generated)",
  AI_ASSISTED: "var(--verdict-ai-assisted)",
  INSUFFICIENT_EVIDENCE: "var(--verdict-insufficient)",
  MIXED_SIGNALS: "var(--verdict-mixed)",
};

interface VerdictBadgeProps {
  verdict: VerdictType;
  className?: string;
}

export function verdictColor(verdict: VerdictType): string {
  return VERDICT_COLOR_VAR[verdict];
}

export function verdictDisplayText(verdict: VerdictType): string {
  return VERDICT_DISPLAY[verdict];
}

export function VerdictBadge({ verdict, className }: VerdictBadgeProps) {
  const color = VERDICT_COLOR_VAR[verdict];
  return (
    <span
      className={cn(
        "inline-flex w-fit shrink-0 items-center rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        className,
      )}
      style={{
        color,
        borderColor: color,
        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
      }}
    >
      {VERDICT_DISPLAY[verdict]}
    </span>
  );
}
