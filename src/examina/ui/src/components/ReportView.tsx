import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ReportHeader } from "@/components/cards/ReportHeader";
import { ExpiryBanner } from "@/components/cards/ExpiryBanner";
import { AssessmentCard } from "@/components/cards/AssessmentCard";
import { HistoryCard } from "@/components/cards/HistoryCard";
import { EvidenceCard } from "@/components/cards/EvidenceCard";
import { ConfidenceCard } from "@/components/cards/ConfidenceCard";
import { FeedbackCard } from "@/components/cards/FeedbackCard";
import type { AnalyzeResponse, ExaminaReport } from "@/lib/types";

interface ReportViewProps {
  report: ExaminaReport;
  analyzeResponse: AnalyzeResponse;
  inviteCode: string;
  onBack: () => void;
}

export function ReportView({ report, analyzeResponse, onBack }: ReportViewProps) {
  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto flex max-w-[800px] flex-col gap-4">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="w-fit gap-1.5"
        >
          <ArrowLeft className="size-4" />
          New Analysis
        </Button>

        <ReportHeader report={report} />
        <ExpiryBanner report={report} />
        <AssessmentCard assessment={report.assessment} />
        <HistoryCard history={report.history} />
        <EvidenceCard evidence={report.evidence} />
        <ConfidenceCard
          confidence={report.confidence}
          activeHypotheses={analyzeResponse.active_hypotheses}
          unresolvedContradictions={analyzeResponse.unresolved_contradictions}
        />
        <FeedbackCard reportId={report.report_id} />
      </div>
    </div>
  );
}
