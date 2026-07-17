import { useEffect, useState } from "react";
import { Clock } from "lucide-react";

import { CopyButton } from "@/components/ui/CopyButton";
import type { ExaminaReport } from "@/lib/types";

interface ExpiryBannerProps {
  report: ExaminaReport;
}

function computeRemaining(expiresAt: string): { hours: number; minutes: number } | null {
  const diffMs = new Date(expiresAt).getTime() - Date.now();
  if (diffMs <= 0) return null;
  const totalMinutes = Math.floor(diffMs / 60000);
  return { hours: Math.floor(totalMinutes / 60), minutes: totalMinutes % 60 };
}

export function ExpiryBanner({ report }: ExpiryBannerProps) {
  const [remaining, setRemaining] = useState(() => computeRemaining(report.expires_at));

  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining(computeRemaining(report.expires_at));
    }, 60_000);
    return () => clearInterval(interval);
  }, [report.expires_at]);

  if (!remaining) return null;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[color-mix(in_srgb,#ca8a04_40%,transparent)] bg-[color-mix(in_srgb,#ca8a04_15%,transparent)] px-4 py-3 text-sm text-foreground">
      <div className="flex items-center gap-2">
        <Clock className="size-4 shrink-0 text-[#ca8a04]" />
        <span>
          This report will be deleted in {remaining.hours}h {remaining.minutes}m. Download the
          JSON to keep a permanent copy.
        </span>
      </div>
      <CopyButton value={JSON.stringify(report, null, 2)} label="Copy Report JSON" />
    </div>
  );
}
