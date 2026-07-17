import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CopyButton } from "@/components/ui/CopyButton";
import { reportIncorrect } from "@/lib/api";
import type { ExaminaReport } from "@/lib/types";

interface ReportHeaderProps {
  report: ExaminaReport;
}

function formatTimestamp(isoString: string): string {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function ReportHeader({ report }: ReportHeaderProps) {
  const [panelOpen, setPanelOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmitIncorrect(): Promise<void> {
    setSubmitting(true);
    await reportIncorrect(report.report_id, comment || null);
    setSubmitting(false);
    setSubmitted(true);
  }

  function handleCancel(): void {
    setPanelOpen(false);
    setComment("");
  }

  const truncatedHash = `${report.file_hash.slice(0, 16)}...`;

  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">EXAMINA Analysis Report</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {formatTimestamp(report.created_at)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{report.file_type}</Badge>
            <Badge variant="secondary" className="font-mono text-[10px] text-muted-foreground">
              v{report.examina_version}
            </Badge>
          </div>
        </div>

        <div className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <p className="text-xs text-muted-foreground">Report ID</p>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs">{report.report_id}</span>
              <CopyButton value={report.report_id} label="Copy" />
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">SHA-256</p>
            <span className="font-mono text-xs" title={report.file_hash}>
              {truncatedHash}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <CopyButton
            value={JSON.stringify(report, null, 2)}
            label="Copy Report JSON"
          />
          <Button type="button" variant="secondary" size="sm" onClick={() => setPanelOpen((v) => !v)}>
            Report Incorrect Analysis
          </Button>
        </div>

        {panelOpen && (
          <div className="rounded-md border border-border bg-muted/30 p-3">
            {submitted ? (
              <p className="text-sm">Thank you.</p>
            ) : (
              <div className="flex flex-col gap-2">
                <p className="text-sm text-muted-foreground">
                  If this analysis produced incorrect results, please let us know. Your file is
                  not stored.
                </p>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value.slice(0, 500))}
                  maxLength={500}
                  placeholder="Optional comment"
                  className="min-h-20 rounded-md border border-border bg-input p-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
                />
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="ghost" size="sm" onClick={handleCancel}>
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    disabled={submitting}
                    onClick={() => void handleSubmitIncorrect()}
                  >
                    Submit
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
