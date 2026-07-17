import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ConfidenceBar, confidenceColor } from "@/components/ui/ConfidenceBar";
import type { ConfidenceDimension, ConfidenceSection } from "@/lib/types";

interface ConfidenceCardProps {
  confidence: ConfidenceSection;
  activeHypotheses: number;
  unresolvedContradictions: number;
}

const DIMENSION_ORDER: Array<{ key: keyof ConfidenceSection; label: string }> = [
  { key: "extraction", label: "Signal Extraction" },
  { key: "reliability", label: "Source Reliability" },
  { key: "inference", label: "Inference Strength" },
  { key: "hypothesis", label: "Hypothesis Support" },
  { key: "penalty", label: "Contradiction Penalty" },
];

export function ConfidenceCard({
  confidence,
  activeHypotheses,
  unresolvedContradictions,
}: ConfidenceCardProps) {
  const [cascadeOpen, setCascadeOpen] = useState(false);
  const overallColor = confidenceColor(confidence.overall);
  const penaltyPercent = Math.round(confidence.penalty.value * 100);

  return (
    <Card>
      <CardContent className="flex flex-col gap-5">
        <h2 className="text-base font-semibold">Confidence Assessment</h2>

        <div>
          <span className="text-4xl font-bold" style={{ color: overallColor }}>
            {Math.round(confidence.overall * 100)}%
          </span>
          <p className="text-sm text-muted-foreground">Overall confidence ({confidence.overall_label})</p>
        </div>

        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="rounded-md border border-border p-2">
            <p
              className="text-lg font-semibold"
              style={{ color: penaltyPercent > 5 ? "var(--verdict-manipulated)" : undefined }}
            >
              {penaltyPercent > 5 ? `-${penaltyPercent}%` : `${penaltyPercent}%`}
            </p>
            <p className="text-xs text-muted-foreground">Contradiction penalty</p>
          </div>
          <div className="rounded-md border border-border p-2">
            <p className="text-lg font-semibold">{unresolvedContradictions}</p>
            <p className="text-xs text-muted-foreground">Unresolved contradictions</p>
          </div>
          <div className="rounded-md border border-border p-2">
            <p className="text-lg font-semibold">{activeHypotheses}</p>
            <p className="text-xs text-muted-foreground">Active hypotheses</p>
          </div>
        </div>

        <Collapsible open={cascadeOpen} onOpenChange={setCascadeOpen}>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md border border-border bg-muted/30 px-3 py-2 text-left text-sm font-medium">
            Show confidence breakdown
            <ChevronDown
              className={`size-4 shrink-0 transition-transform ${cascadeOpen ? "rotate-180" : ""}`}
            />
          </CollapsibleTrigger>
          <CollapsibleContent className="flex flex-col gap-4 rounded-b-md border border-t-0 border-border p-3">
            {DIMENSION_ORDER.map(({ key, label }) => {
              const dimension = confidence[key] as ConfidenceDimension;
              const isPenalty = key === "penalty";
              const colorOverride =
                isPenalty && dimension.value > 0 ? "var(--verdict-manipulated)" : undefined;
              return (
                <div key={key} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-foreground">{label}</span>
                    <span className="text-muted-foreground">
                      {Math.round(dimension.value * 100)}%
                    </span>
                  </div>
                  <ConfidenceBar value={dimension.value} colorOverride={colorOverride} />
                  <p className="text-xs text-muted-foreground">{dimension.note.text}</p>
                </div>
              );
            })}
          </CollapsibleContent>
        </Collapsible>

        <div>
          <h3 className="text-sm font-medium text-foreground">Known Limitations</h3>
          <ul className="mt-1 list-disc pl-5">
            {confidence.limitations.map((limitation) => (
              <li key={limitation} className="text-sm text-muted-foreground">
                {limitation}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-muted-foreground">{confidence.disclaimer}</p>
      </CardContent>
    </Card>
  );
}
