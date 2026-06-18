"use client";

import React, { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { GitCompare, ArrowLeft, Loader2, Globe } from "lucide-react";

export default function ComparePage() {
  const router = useRouter();
  const [companyA, setCompanyA] = useState("");
  const [urlA, setUrlA] = useState("");
  const [companyB, setCompanyB] = useState("");
  const [urlB, setUrlB] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValid = useMemo(
    () => companyA.trim().length >= 2 && companyB.trim().length >= 2,
    [companyA, companyB]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!isValid || submitting) return;
      setSubmitting(true);
      setError(null);
      try {
        const res = await fetch("/api/research/compare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            company_a: companyA.trim(),
            company_b: companyB.trim(),
            website_url_a: urlA.trim() || null,
            website_url_b: urlB.trim() || null,
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }
        const data = await res.json();
        router.push(`/compare/${data.compare_job_id}`);
      } catch (err) {
        setError((err as Error).message);
        setSubmitting(false);
      }
    },
    [companyA, urlA, companyB, urlB, isValid, submitting, router]
  );

  return (
    <div className="min-h-screen px-4 py-16 max-w-3xl mx-auto">
      <button
        onClick={() => router.push("/")}
        className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors mb-8"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-3 mb-3">
          <GitCompare className="w-8 h-8 text-blue-400" />
          <h1 className="text-4xl font-bold text-white">Compare Companies</h1>
        </div>
        <p className="text-zinc-400 max-w-xl mx-auto">
          Run side-by-side competitive intelligence on two companies. Both
          research plans auto-execute and a comparator agent synthesizes the
          differences.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-zinc-900 border border-zinc-700 rounded-xl p-6 space-y-6"
      >
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-blue-400">Company A</h2>
            <input
              type="text"
              value={companyA}
              onChange={(e) => setCompanyA(e.target.value)}
              placeholder="e.g., Notion"
              disabled={submitting}
              className="w-full px-4 py-3 rounded-lg bg-zinc-800 border border-zinc-700
                         text-white placeholder-zinc-500
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="text"
                value={urlA}
                onChange={(e) => setUrlA(e.target.value)}
                placeholder="Optional URL"
                disabled={submitting}
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-zinc-800/60 border border-zinc-700
                           text-zinc-200 placeholder-zinc-600 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-purple-400">Company B</h2>
            <input
              type="text"
              value={companyB}
              onChange={(e) => setCompanyB(e.target.value)}
              placeholder="e.g., Coda"
              disabled={submitting}
              className="w-full px-4 py-3 rounded-lg bg-zinc-800 border border-zinc-700
                         text-white placeholder-zinc-500
                         focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="text"
                value={urlB}
                onChange={(e) => setUrlB(e.target.value)}
                placeholder="Optional URL"
                disabled={submitting}
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-zinc-800/60 border border-zinc-700
                           text-zinc-200 placeholder-zinc-600 text-sm
                           focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="px-4 py-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!isValid || submitting}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg
                     bg-blue-600 text-white font-medium hover:bg-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors duration-200"
        >
          {submitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Starting comparison…
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4" />
              Compare {companyA || "A"} vs {companyB || "B"}
            </>
          )}
        </button>

        <p className="text-xs text-zinc-500 text-center">
          Note: Comparison auto-approves both research plans (no manual
          approval step). Token usage is roughly 2× a single run plus a
          synthesis pass.
        </p>
      </form>
    </div>
  );
}
