import { AlertTriangle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import type { CertaintyType, HistorySection } from "@/lib/types";

const CERTAINTY_COLOR: Record<CertaintyType, string> = {
  CONFIRMED: "var(--confidence-high)",
  PROBABLE: "var(--fact-provenance)",
  INFERRED: "var(--confidence-medium)",
};

const CERTAINTY_LABEL: Record<CertaintyType, string> = {
  CONFIRMED: "Confirmed",
  PROBABLE: "Probable",
  INFERRED: "Inferred",
};

interface HistoryCardProps {
  history: HistorySection;
}

export function HistoryCard({ history }: HistoryCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <h2 className="text-base font-semibold">Most Probable Processing History</h2>

        {!history.reconstruction_complete && (
          <div className="flex items-start gap-2 rounded-md border border-[color-mix(in_srgb,#ca8a04_40%,transparent)] bg-[color-mix(in_srgb,#ca8a04_15%,transparent)] p-3 text-sm text-foreground">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-[#ca8a04]" />
            <span>Reconstruction is incomplete — some events could not be determined.</span>
          </div>
        )}

        {history.unknown_gaps.length > 0 && (
          <ul className="flex flex-col gap-1">
            {history.unknown_gaps.map((gap) => (
              <li key={gap} className="text-sm text-muted-foreground">
                {gap}
              </li>
            ))}
          </ul>
        )}

        <ol className="flex flex-col gap-4">
          {history.events.map((event) => {
            const color = CERTAINTY_COLOR[event.certainty];
            return (
              <li key={event.sequence} className="flex gap-3">
                <div
                  className="flex size-6 shrink-0 items-center justify-center rounded-full border text-xs font-semibold"
                  style={{
                    color,
                    borderColor: color,
                    backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
                  }}
                >
                  {event.sequence}
                </div>
                <div className="flex flex-col gap-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm text-foreground">{event.description.text}</p>
                    <span
                      className="inline-flex w-fit items-center rounded-full border px-2 py-0.5 text-[10px] font-medium"
                      style={{ color, borderColor: color }}
                    >
                      {CERTAINTY_LABEL[event.certainty]}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{event.certainty_note.text}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
