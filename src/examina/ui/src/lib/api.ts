import type { AnalyzeResponse, ReportResponse } from "@/lib/types";

// Empty string keeps requests same-origin so the Vite dev proxy (see vite.config.ts)
// forwards them to the API without a CORS round-trip. Set VITE_API_BASE to point at
// a different host (e.g. a non-proxied production API).
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail ?? body.error ?? message;
    } catch {
      // response was not JSON
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function analyzeFile(file: File, inviteCode: string): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { Authorization: `Bearer ${inviteCode}` },
    body: form,
  });
  return handleResponse<AnalyzeResponse>(res);
}

export async function fetchReport(reportId: string, inviteCode: string): Promise<ReportResponse> {
  const res = await fetch(`${API_BASE}/report/${reportId}`, {
    headers: { Authorization: `Bearer ${inviteCode}` },
  });
  return handleResponse<ReportResponse>(res);
}

export async function deleteReport(reportId: string, inviteCode: string): Promise<void> {
  const res = await fetch(`${API_BASE}/report/${reportId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${inviteCode}` },
  });
  await handleResponse<unknown>(res);
}

export async function submitFeedback(feedback: Record<string, unknown>): Promise<void> {
  try {
    await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(feedback),
    });
  } catch {
    // Never throw on feedback failure — Constitution Principle 6 exception:
    // feedback failure must never interrupt the user's experience.
  }
}

export async function reportIncorrect(reportId: string, userComment: string | null): Promise<void> {
  try {
    await fetch(`${API_BASE}/report-incorrect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report_id: reportId, user_comment: userComment }),
    });
  } catch {
    // Never throw — same rationale as submitFeedback.
  }
}
