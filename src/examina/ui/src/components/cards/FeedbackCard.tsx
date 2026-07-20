import { useState } from "react";
import { Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { submitFeedback } from "@/lib/api";

type SectionValue = "assessment" | "history" | "evidence" | "confidence" | "none";
type ChangedAssessment =
  | "yes_significantly"
  | "yes_somewhat"
  | "no"
  | "unsure_before_and_after";
type WorkflowAdoption = "yes" | "maybe" | "no";

const SECTION_OPTIONS: { value: SectionValue; label: string }[] = [
  { value: "assessment", label: "Assessment" },
  { value: "history", label: "Processing History" },
  { value: "evidence", label: "Evidence" },
  { value: "confidence", label: "Confidence" },
  { value: "none", label: "None" },
];

const CHANGED_ASSESSMENT_OPTIONS: { value: ChangedAssessment; label: string }[] = [
  { value: "yes_significantly", label: "Yes, significantly" },
  { value: "yes_somewhat", label: "Yes, somewhat" },
  { value: "no", label: "No" },
  { value: "unsure_before_and_after", label: "I was unsure before and remain unsure" },
];

interface FeedbackCardProps {
  reportId: string;
}

export function FeedbackCard({ reportId }: FeedbackCardProps) {
  const [understandabilityScore, setUnderstandabilityScore] = useState<number | null>(null);
  const [mostUsefulSection, setMostUsefulSection] = useState<SectionValue | null>(null);
  const [leastUsefulSection, setLeastUsefulSection] = useState<SectionValue | null>(null);
  const [changedAssessment, setChangedAssessment] = useState<ChangedAssessment | null>(null);
  const [wouldUseInWorkflow, setWouldUseInWorkflow] = useState<WorkflowAdoption | null>(null);
  const [missingInformation, setMissingInformation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(): Promise<void> {
    setSubmitting(true);
    await submitFeedback({
      report_id: reportId,
      understandability_score: understandabilityScore,
      most_useful_section: mostUsefulSection,
      least_useful_section: leastUsefulSection,
      changed_assessment: changedAssessment,
      would_use_in_workflow: wouldUseInWorkflow,
      missing_information: missingInformation || null,
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
          <p className="text-sm font-medium">Was this report easy to understand?</p>
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
          <p className="text-sm font-medium">Which section was most useful?</p>
          <div className="flex flex-wrap gap-2">
            {SECTION_OPTIONS.map((option) => (
              <Button
                key={option.value}
                type="button"
                size="sm"
                variant={mostUsefulSection === option.value ? "default" : "outline"}
                onClick={() => setMostUsefulSection(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Which section was least useful?</p>
          <div className="flex flex-wrap gap-2">
            {SECTION_OPTIONS.map((option) => (
              <Button
                key={option.value}
                type="button"
                size="sm"
                variant={leastUsefulSection === option.value ? "default" : "outline"}
                onClick={() => setLeastUsefulSection(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Did this report change your assessment of the file?</p>
          <div className="flex flex-wrap gap-2">
            {CHANGED_ASSESSMENT_OPTIONS.map((option) => (
              <Button
                key={option.value}
                type="button"
                size="sm"
                variant={changedAssessment === option.value ? "default" : "outline"}
                onClick={() => setChangedAssessment(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">
            Would you use this in your normal verification workflow?
          </p>
          <div className="flex gap-2">
            {(["yes", "maybe", "no"] as const).map((option) => (
              <Button
                key={option}
                type="button"
                size="sm"
                variant={wouldUseInWorkflow === option ? "default" : "outline"}
                onClick={() => setWouldUseInWorkflow(option)}
                className="capitalize"
              >
                {option}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="feedback-missing-information" className="text-sm font-medium">
            What information was missing?
          </label>
          <textarea
            id="feedback-missing-information"
            value={missingInformation}
            onChange={(e) => setMissingInformation(e.target.value.slice(0, 500))}
            maxLength={500}
            placeholder="What would have helped you make a better decision?"
            className="min-h-20 rounded-md border border-border bg-input p-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
          />
          <span className="self-end text-xs text-muted-foreground">
            {missingInformation.length}/500
          </span>
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
