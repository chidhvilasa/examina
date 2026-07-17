import { useRef, useState } from "react";
import { AlertCircle, Loader2, Upload, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { analyzeFile, fetchReport } from "@/lib/api";
import type { AnalyzeResponse, ExaminaReport } from "@/lib/types";

const ACCEPTED_MIME_TYPES = "image/jpeg,image/png,image/webp,application/pdf";
const ACCEPTED_MIME_SET = new Set(ACCEPTED_MIME_TYPES.split(","));
const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024;

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface UploadViewProps {
  inviteCode: string;
  isAnalyzing: boolean;
  error: string | null;
  onInviteCodeChange: (inviteCode: string) => void;
  onAnalysisStart: () => void;
  onAnalysisError: (error: string) => void;
  onAnalysisSuccess: (analyzeResponse: AnalyzeResponse, report: ExaminaReport) => void;
  onDismissError: () => void;
}

export function UploadView({
  inviteCode,
  isAnalyzing,
  error,
  onInviteCodeChange,
  onAnalysisStart,
  onAnalysisError,
  onAnalysisSuccess,
  onDismissError,
}: UploadViewProps) {
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function validateAndSetFile(candidate: File): void {
    if (!ACCEPTED_MIME_SET.has(candidate.type)) {
      setFileError("This file type is not supported.");
      setFile(null);
      return;
    }
    if (candidate.size > MAX_FILE_SIZE_BYTES) {
      setFileError("This file exceeds the 20MB limit.");
      setFile(null);
      return;
    }
    setFileError(null);
    setFile(candidate);
  }

  function handleFileInputChange(e: React.ChangeEvent<HTMLInputElement>): void {
    const candidate = e.target.files?.[0];
    if (candidate) validateAndSetFile(candidate);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>): void {
    e.preventDefault();
    setIsDragging(false);
    const candidate = e.dataTransfer.files?.[0];
    if (candidate) validateAndSetFile(candidate);
  }

  async function runAnalysis(): Promise<void> {
    if (!file || !inviteCode || isAnalyzing) return;
    onAnalysisStart();
    try {
      const analyzeResponse = await analyzeFile(file, inviteCode);
      const reportResponse = await fetchReport(analyzeResponse.report_id, inviteCode);
      onAnalysisSuccess(analyzeResponse, reportResponse.report);
    } catch (err) {
      onAnalysisError(err instanceof Error ? err.message : "Analysis failed.");
    }
  }

  function handleInviteCodeKeyDown(e: React.KeyboardEvent<HTMLInputElement>): void {
    if (e.key === "Enter" && file && inviteCode) {
      void runAnalysis();
    }
  }

  const canAnalyze = Boolean(file && inviteCode) && !isAnalyzing;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-[560px]">
        <CardHeader className="items-center text-center">
          <h1 className="text-3xl font-bold text-primary">EXAMINA</h1>
          <p className="text-sm text-muted-foreground">Digital Evidence Intelligence</p>
          <Badge variant="secondary" className="mt-1">
            Research Beta
          </Badge>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              isDragging ? "border-primary bg-primary/5" : "border-border"
            }`}
          >
            <Upload className="size-8 text-muted-foreground" />
            {file ? (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{file.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({formatFileSize(file.size)})
                </span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    setFileError(null);
                    if (inputRef.current) inputRef.current.value = "";
                  }}
                  aria-label="Remove selected file"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="size-4" />
                </button>
              </div>
            ) : (
              <p className="text-sm text-foreground">Drop a file here or click to browse</p>
            )}
            <p className="text-xs text-muted-foreground">
              Accepted: JPEG, PNG, WebP, PDF — max 20MB
            </p>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_MIME_TYPES}
              onChange={handleFileInputChange}
              className="hidden"
            />
          </div>
          {fileError && (
            <p className="text-sm text-destructive" role="alert">
              {fileError}
            </p>
          )}

          <div className="flex flex-col gap-1.5">
            <label htmlFor="invite-code" className="text-sm font-medium">
              Invite Code
            </label>
            <input
              id="invite-code"
              type="password"
              placeholder="Enter your invite code"
              value={inviteCode}
              onChange={(e) => onInviteCodeChange(e.target.value)}
              onKeyDown={handleInviteCodeKeyDown}
              className="h-9 rounded-md border border-border bg-input px-3 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50"
            />
          </div>

          <Button
            type="button"
            disabled={!canAnalyze}
            onClick={() => void runAnalysis()}
            className="gap-2"
          >
            {isAnalyzing && <Loader2 className="size-4 animate-spin" />}
            {isAnalyzing ? "Analyzing..." : "Analyze File"}
          </Button>

          {error && (
            <div className="flex items-start justify-between gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{error}</span>
              </div>
              <button
                type="button"
                onClick={onDismissError}
                aria-label="Dismiss error"
                className="text-destructive hover:opacity-70"
              >
                <X className="size-4" />
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
