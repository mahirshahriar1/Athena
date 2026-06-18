"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import {
  ArrowLeft,
  Loader2,
  GitCompare,
  FileText,
  Download,
  Coins,
} from "lucide-react";

interface ReportResponse {
  job_id: string;
  status: string;
  report: string | null;
  tokens: {
    input: number;
    output: number;
    total: number;
    calls: number;
  } | null;
}

interface StatusResponse {
  job_id: string;
  status: string;
  current_node: string | null;
  plan: string[];
  company: string;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export default function CompareResultPage() {
  const params = useParams();
  const router = useRouter();
  const compareJobId = params.compareJobId as string;

  const [status, setStatus] = useState<string>("running");
  const [company, setCompany] = useState<string>("");
  const [report, setReport] = useState<string | null>(null);
  const [tokens, setTokens] = useState<ReportResponse["tokens"]>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`/api/research/${compareJobId}/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as StatusResponse;
      setStatus(data.status);
      setCompany(data.company);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [compareJobId]);

  const fetchReport = useCallback(async () => {
    try {
      const res = await fetch(`/api/research/${compareJobId}/report`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as ReportResponse;
      setReport(data.report);
      setTokens(data.tokens);
      if (data.status === "completed") {
        setStatus("completed");
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }, [compareJobId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    if (status === "completed") {
      fetchReport();
      return;
    }
    if (status === "error") return;
    const interval = setInterval(() => {
      fetchStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, [status, fetchStatus, fetchReport]);

  const handleDownload = useCallback(() => {
    if (!report) return;
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${company.toLowerCase().replace(/\s+/g, "-")}-comparison.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [report, company]);

  const tokenSummary = useMemo(() => {
    if (!tokens || tokens.total === 0) return null;
    return formatTokens(tokens.total);
  }, [tokens]);

  return (
    <div className="min-h-screen px-4 py-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="flex items-center gap-3">
          {tokenSummary && (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md
                         bg-amber-900/20 border border-amber-700/30 text-amber-300 text-xs"
              title={`${tokens?.calls} LLM calls`}
            >
              <Coins className="w-3 h-3" />
              {tokenSummary} tokens
            </span>
          )}
          <span
            className={`text-xs px-2 py-1 rounded ${
              status === "completed"
                ? "bg-green-900/20 text-green-400"
                : status === "error"
                ? "bg-red-900/20 text-red-400"
                : "bg-blue-900/20 text-blue-400"
            }`}
          >
            {status.replace("_", " ")}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <GitCompare className="w-7 h-7 text-blue-400" />
        <h1 className="text-3xl font-bold text-white">{company || "Comparison"}</h1>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {status !== "completed" && status !== "error" && (
        <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-12 flex flex-col items-center justify-center gap-4">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
          <p className="text-zinc-300 text-sm">
            Both research pipelines are running in parallel. This usually takes
            5–10 minutes.
          </p>
          <p className="text-zinc-500 text-xs">
            You can leave this page open — it polls every 5 seconds.
          </p>
        </div>
      )}

      {report && (
        <div className="bg-zinc-900 border border-zinc-700 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-zinc-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-semibold text-white">
                Comparison Report
              </h2>
            </div>
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-3 py-2 rounded-lg
                         bg-zinc-800 text-zinc-300 text-sm hover:bg-zinc-700
                         transition-colors duration-200"
            >
              <Download className="w-4 h-4" />
              Download .md
            </button>
          </div>
          <div className="p-6 prose prose-invert prose-zinc max-w-none
                          prose-headings:text-zinc-100 prose-p:text-zinc-300
                          prose-li:text-zinc-300 prose-strong:text-white
                          prose-a:text-blue-400 prose-code:text-green-400
                          prose-table:text-zinc-300 prose-th:text-white">
            <ReactMarkdown>{report}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
