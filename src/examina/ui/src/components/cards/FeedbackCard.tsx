import { useState } from "react";
import { Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { submitFeedback } from "@/lib/api";

type ConclusionCorrect = "yes" | "no" | "unsure";

const CONFUSING_SECTION_OPTIONS = [
  { value: "", label: "None" },
  { value: "Assessment", label: "Assessment" },
  { value: "Processing History", label: "Processing History" },
  { value: "Evidence", label: "Evidence" },
  { value: "Confidence", label: "Confidence" },
  { value: "Overall", label: "Overall" },
];

interface FeedbackCardProps {
  reportId: string;
}

export function FeedbackCard({ reportId }: FeedbackCardProps) {
  const [understandabilityScore, setUnderstandabilityScore] = useState<number | null>(null);
  const [conclusionCorrect, setConclusionCorrect] = useState<ConclusionCorrect | null>(null);
  const [confusingSection, setConfusingSection] = useState("");
  const [analysisDurationOk, setAnalysisDurationOk] = useState<boolean | null>(null);
  const [wouldTrust, setWouldTrust] = useState<boolean | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(): Promise<void> {
    setSubmitting(true);
    await submitFeedback({
      report_id: reportId,
      understandability_score: understandabilityScore,
      conclusion_correct: conclusionCorrect,
      confusing_section: confusingSection || null,
      analysis_duration_ok: analysisDurationOk,
      would_trust: wouldTrust,
      optional_comment: comment || null,
    });
    setSubmitting(false);
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <Card>
        <CardContent>
          <p className="text-sm text-foreground">Thank you. Your feedback has been recorded.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-5">
        <div>
          <h2 className="text-base font-semibold">Help Improve EXAMINA</h2>
          <p className="text-sm text-muted-foreground">
            This tool is in research beta. Your feedback directly shapes improvements.
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">How understandable was this report?</p>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setUnderstandabilityScore(n)}
                aria-label={`${n} star${n === 1 ? "" : "s"}`}
                className="text-muted-foreground"
              >
                <Star
                  className="size-5"
                  fill={understandabilityScore !== null && n <= understandabilityScore ? "currentColor" : "none"}
                  style={{
                    color:
                      understandabilityScore !== null && n <= understandabilityScore
                        ? "var(--confidence-medium)"
                        : undefined,
                  }}
                />
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Was the conclusion correct?</p>
          <div className="flex gap-2">
            {(["yes", "no", "unsure"] as const).map((option) => (
              <Button
                key={option}
                type="button"
                size="sm"
                variant={conclusionCorrect === option ? "default" : "outline"}
                onClick={() => setConclusionCorrect(option)}
                className="capitalize"
              >
                {option}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="confusing-section" className="text-sm font-medium">
            Which section confused you most?
          </label>
          <select
            id="confusing-section"
            value={confusingSection}
            onChange={(e) => setConfusingSection(e.target.value)}
            className="h-9 rounded-md border border-border bg-input px-2 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
          >
            {CONFUSING_SECTION_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Was the analysis fast enough?</p>
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant={analysisDurationOk === true ? "default" : "outline"}
              onClick={() => setAnalysisDurationOk(true)}
            >
              Yes
            </Button>
            <Button
              type="button"
              size="sm"
              variant={analysisDurationOk === false ? "default" : "outline"}
              onClick={() => setAnalysisDurationOk(false)}
            >
              No
            </Button>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Would you trust this report professionally?</p>
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant={wouldTrust === true ? "default" : "outline"}
              onClick={() => setWouldTrust(true)}
            >
              Yes
            </Button>
            <Button
              type="button"
              size="sm"
              variant={wouldTrust === false ? "default" : "outline"}
              onClick={() => setWouldTrust(false)}
            >
              No
            </Button>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="feedback-comment" className="text-sm font-medium">
            Additional comments (max 500 chars)
          </label>
          <textarea
            id="feedback-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value.slice(0, 500))}
            maxLength={500}
            className="min-h-20 rounded-md border border-border bg-input p-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
          />
          <span className="self-end text-xs text-muted-foreground">{comment.length}/500</span>
        </div>

        <Button
          type="button"
          disabled={submitting}
          onClick={() => void handleSubmit()}
          className="self-start"
        >
          Submit Feedback
        </Button>
      </CardContent>
    </Card>
  );
}
