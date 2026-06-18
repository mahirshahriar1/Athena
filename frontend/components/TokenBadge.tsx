"use client";

import React, { useMemo } from "react";
import { Coins } from "lucide-react";
import { TokenUsage } from "@/lib/slices/researchSlice";

interface TokenBadgeProps {
  tokens: TokenUsage | null;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

const TokenBadge = React.memo(function TokenBadge({ tokens }: TokenBadgeProps) {
  const summary = useMemo(() => {
    if (!tokens || tokens.total === 0) return null;
    return {
      total: formatTokens(tokens.total),
      input: formatTokens(tokens.input),
      output: formatTokens(tokens.output),
      calls: tokens.calls,
    };
  }, [tokens]);

  if (!summary) return null;

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md
                 bg-amber-900/20 border border-amber-700/30 text-amber-300 text-xs"
      title={`Input: ${summary.input} · Output: ${summary.output} · ${summary.calls} LLM calls`}
    >
      <Coins className="w-3 h-3" />
      {summary.total} tokens
    </span>
  );
});

export default TokenBadge;
