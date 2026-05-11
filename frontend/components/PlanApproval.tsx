"use client";

import React, { useCallback } from "react";
import { CheckCircle, XCircle, ListChecks } from "lucide-react";

interface PlanApprovalProps {
  plan: string[];
  company: string;
  onApprove: () => void;
  onReject: () => void;
  isLoading: boolean;
}

const PlanApproval = React.memo(function PlanApproval({
  plan,
  company,
  onApprove,
  onReject,
  isLoading,
}: PlanApprovalProps) {
  const handleApprove = useCallback(() => {
    if (!isLoading) onApprove();
  }, [isLoading, onApprove]);

  const handleReject = useCallback(() => {
    if (!isLoading) onReject();
  }, [isLoading, onReject]);

  return (
    <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-700 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <ListChecks className="w-6 h-6 text-blue-400" />
        <h2 className="text-xl font-semibold text-white">
          Research Plan for{" "}
          <span className="text-blue-400">{company}</span>
        </h2>
      </div>

      <p className="text-zinc-400 text-sm mb-4">
        Review the research tasks below. Approve to start the AI agents.
      </p>

      <ul className="space-y-2 mb-6">
        {plan.map((task, i) => (
          <li
            key={i}
            className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50"
          >
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600/20 text-blue-400
                           flex items-center justify-center text-xs font-medium">
              {i + 1}
            </span>
            <span className="text-zinc-200 text-sm">{task}</span>
          </li>
        ))}
      </ul>

      <div className="flex gap-3">
        <button
          onClick={handleApprove}
          disabled={isLoading}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg
                     bg-green-600 text-white font-medium hover:bg-green-500
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors duration-200"
        >
          <CheckCircle className="w-5 h-5" />
          {isLoading ? "Running Agents..." : "Approve & Start Research"}
        </button>
        <button
          onClick={handleReject}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg
                     bg-zinc-700 text-zinc-300 font-medium hover:bg-zinc-600
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors duration-200"
        >
          <XCircle className="w-5 h-5" />
          Cancel
        </button>
      </div>
    </div>
  );
});

export default PlanApproval;
