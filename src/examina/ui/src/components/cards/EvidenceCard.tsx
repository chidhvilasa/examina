import { useState } from "react";
import { CheckCircle2, ChevronDown, Circle, XCircle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { EvidenceFamily, EvidenceSection, Signal, SignalDirection } from "@/lib/types";

const DIRECTION_ICON: Record<SignalDirection, React.ReactNode> = {
  SUPPORTS: <CheckCircle2 className="size-4 shrink-0 text-[var(--confidence-high)]" />,
  CONTRADICTS: <XCircle className="size-4 shrink-0 text-[var(--verdict-manipulated)]" />,
  NEUTRAL: <Circle className="size-3 shrink-0 fill-current text-muted-foreground" />,
};

function SignalRow({ signal }: { signal: Signal }) {
  return (
    <li className="flex items-start gap-2 py-2">
      {DIRECTION_ICON[signal.direction]}
      <div className="flex flex-1 flex-col gap-0.5">
        <p className="text-sm text-foreground">{signal.statement.text}</p>
        <p className="text-xs text-muted-foreground">
          {Math.round(signal.extraction_confidence * 100)}% extraction confidence —{" "}
          <span className="text-muted-foreground">{signal.produced_by}</span>
        </p>
      </div>
    </li>
  );
}

function EvidenceFamilyBlock({ family }: { family: EvidenceFamily }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-foreground">{family.family_name}</h3>
        {!family.correlated && (
          <span className="text-xs text-muted-foreground">
            {family.signals.length} signal{family.signals.length === 1 ? "" : "s"}
          </span>
        )}
      </div>
      <p className="text-sm font-medium text-foreground">{family.family_finding.text}</p>

      {family.correlated && (
        <p className="text-xs text-muted-foreground">
          These signals are correlated and represent a single cluster of evidence, not
          independent votes.
        </p>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 self-start text-xs font-medium text-primary"
      >
        {open ? "Hide" : "Show"} signals
        <ChevronDown className={`size-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <ul className="divide-y divide-border rounded-md border border-border px-3">
          {family.signals.map((signal) => (
            <SignalRow key={signal.signal_id} signal={signal} />
          ))}
        </ul>
      )}
    </div>
  );
}

interface EvidenceCardProps {
  evidence: EvidenceSection;
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-5">
        <h2 className="text-base font-semibold">Forensic Evidence</h2>
        {evidence.families.map((family, index) => (
          <div key={family.family_id} className="flex flex-col gap-3">
            {index > 0 && <Separator />}
            <EvidenceFamilyBlock family={family} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
