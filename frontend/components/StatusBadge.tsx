"use client";

import React, { useMemo } from "react";

interface StatusBadgeProps {
  status: string;
}

const StatusBadge = React.memo(function StatusBadge({ status }: StatusBadgeProps) {
  const config = useMemo(() => {
    switch (status) {
      case "idle":
        return { label: "Idle", color: "bg-zinc-700 text-zinc-300" };
      case "planning":
        return { label: "Planning", color: "bg-yellow-900 text-yellow-300" };
      case "awaiting_approval":
        return { label: "Awaiting Approval", color: "bg-amber-900 text-amber-300" };
      case "running":
        return { label: "Running", color: "bg-blue-900 text-blue-300" };
      case "completed":
        return { label: "Completed", color: "bg-green-900 text-green-300" };
      case "error":
        return { label: "Error", color: "bg-red-900 text-red-300" };
      default:
        return { label: status, color: "bg-zinc-700 text-zinc-300" };
    }
  }, [status]);

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${config.color}`}
    >
      {(status === "running" || status === "planning") && (
        <span className="w-2 h-2 mr-2 rounded-full bg-current animate-pulse" />
      )}
      {config.label}
    </span>
  );
});

export default StatusBadge;
