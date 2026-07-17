import { useState } from "react";
import { CheckCircle2, ChevronDown } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { verdictColor, verdictDisplayText } from "@/components/ui/VerdictBadge";
import type { Assessment, ConfidenceLabelType } from "@/lib/types";

const CONFIDENCE_COLOR_VAR: Record<ConfidenceLabelType, string> = {
  HIGH: "var(--confidence-high)",
  MEDIUM: "var(--confidence-medium)",
  LOW: "var(--confidence-low)",
  INSUFFICIENT: "var(--confidence-insufficient)",
};

interface AssessmentCardProps {
  assessment: Assessment;
}

export function AssessmentCard({ assessment }: AssessmentCardProps) {
  const [whatWouldChangeOpen, setWhatWouldChangeOpen] = useState(true);
  const color = verdictColor(assessment.verdict);
  const confidenceColor = CONFIDENCE_COLOR_VAR[assessment.confidence_label];

  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <div>
          <h2 className="text-2xl font-bold" style={{ color }}>
            {verdictDisplayText(assessment.verdict)}
          </h2>
          <span
            className="mt-2 inline-flex w-fit items-center rounded-full border px-2.5 py-0.5 text-xs font-medium"
            style={{
              color: confidenceColor,
              borderColor: confidenceColor,
              backgroundColor: `color-mix(in srgb, ${confidenceColor} 15%, transparent)`,
            }}
          >
            {assessment.confidence_label} confidence
          </span>
        </div>

        <p className="text-sm leading-relaxed text-foreground">{assessment.verdict_plain.text}</p>

        <div className="rounded-md border border-primary/30 bg-primary/10 p-3">
          <div className="flex items-center gap-2 text-sm font-medium text-primary">
            <CheckCircle2 className="size-4" />
            Recommended Action
          </div>
          <p className="mt-1 text-sm text-foreground">{assessment.recommendation.text}</p>
        </div>

        <Collapsible open={whatWouldChangeOpen} onOpenChange={setWhatWouldChangeOpen}>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md border border-border bg-muted/30 px-3 py-2 text-left text-sm font-medium">
            What would change this conclusion?
            <ChevronDown
              className={`size-4 shrink-0 transition-transform ${whatWouldChangeOpen ? "rotate-180" : ""}`}
            />
          </CollapsibleTrigger>
          <CollapsibleContent className="rounded-b-md border border-t-0 border-border p-3 text-sm text-muted-foreground">
            {assessment.what_would_change.text}
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}
