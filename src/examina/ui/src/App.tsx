import { useState } from "react";

import { UploadView } from "@/components/UploadView";
import { ReportView } from "@/components/ReportView";
import type { AnalyzeResponse, ExaminaReport } from "@/lib/types";

interface AppState {
  view: "upload" | "report";
  inviteCode: string;
  report: ExaminaReport | null;
  analyzeResponse: AnalyzeResponse | null;
  isAnalyzing: boolean;
  error: string | null;
}

const INITIAL_STATE: AppState = {
  view: "upload",
  inviteCode: "",
  report: null,
  analyzeResponse: null,
  isAnalyzing: false,
  error: null,
};

function App() {
  const [state, setState] = useState<AppState>(INITIAL_STATE);

  function handleInviteCodeChange(inviteCode: string): void {
    setState((prev) => ({ ...prev, inviteCode }));
  }

  function handleAnalysisStart(): void {
    setState((prev) => ({ ...prev, isAnalyzing: true, error: null }));
  }

  function handleAnalysisError(error: string): void {
    setState((prev) => ({ ...prev, isAnalyzing: false, error }));
  }

  function handleDismissError(): void {
    setState((prev) => ({ ...prev, error: null }));
  }

  function handleAnalysisSuccess(analyzeResponse: AnalyzeResponse, report: ExaminaReport): void {
    setState((prev) => ({
      ...prev,
      view: "report",
      analyzeResponse,
      report,
      isAnalyzing: false,
      error: null,
    }));
  }

  function handleBackToUpload(): void {
    setState((prev) => ({
      ...INITIAL_STATE,
      inviteCode: prev.inviteCode,
    }));
  }

  if (state.view === "report" && state.report && state.analyzeResponse) {
    return (
      <ReportView
        report={state.report}
        analyzeResponse={state.analyzeResponse}
        inviteCode={state.inviteCode}
        onBack={handleBackToUpload}
      />
    );
  }

  return (
    <UploadView
      inviteCode={state.inviteCode}
      isAnalyzing={state.isAnalyzing}
      error={state.error}
      onInviteCodeChange={handleInviteCodeChange}
      onAnalysisStart={handleAnalysisStart}
      onAnalysisError={handleAnalysisError}
      onAnalysisSuccess={handleAnalysisSuccess}
      onDismissError={handleDismissError}
    />
  );
}

export default App;
