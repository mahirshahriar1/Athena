"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { History, Loader2, GitCompare, FileText } from "lucide-react";

interface HistoryItem {
  job_id: string;
  company: string;
  seed_url: string | null;
  status: string;
  kind: string;
  created_at: string;
  updated_at: string;
}

interface HistoryResponse {
  items: HistoryItem[];
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const sec = Math.max(0, Math.round((now - then) / 1000));
  if (sec < 60) return `${sec}s ago`;
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.round(hr / 24);
  return `${d}d ago`;
}

const STATUS_COLOR: Record<string, string> = {
  completed: "text-green-400 bg-green-900/20",
  running: "text-blue-400 bg-blue-900/20",
  awaiting_approval: "text-amber-400 bg-amber-900/20",
  error: "text-red-400 bg-red-900/20",
};

const HistoryList = React.memo(function HistoryList() {
  const router = useRouter();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/research/history");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as HistoryResponse;
      setItems(data.items);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleClick = useCallback(
    (item: HistoryItem) => {
      if (item.kind === "compare") {
        router.push(`/compare/${item.job_id}`);
      } else {
        router.push(`/research/${item.job_id}`);
      }
    },
    [router]
  );

  const content = useMemo(() => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-6 text-zinc-500 text-sm">
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
          Loading history…
        </div>
      );
    }
    if (error) {
      return (
        <div className="text-red-400 text-sm text-center py-4">
          Failed to load history: {error}
        </div>
      );
    }
    if (items.length === 0) {
      return (
        <div className="text-zinc-500 text-sm text-center py-6">
          No past research runs yet — run your first above.
        </div>
      );
    }
    return (
      <ul className="divide-y divide-zinc-800">
        {items.map((item) => {
          const Icon = item.kind === "compare" ? GitCompare : FileText;
          return (
            <li key={item.job_id}>
              <button
                onClick={() => handleClick(item)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left
                           hover:bg-zinc-800/50 transition-colors duration-150"
              >
                <Icon className="w-4 h-4 text-zinc-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-zinc-200 text-sm font-medium truncate">
                    {item.company}
                  </p>
                  {item.seed_url && (
                    <p className="text-zinc-500 text-xs truncate">
                      {item.seed_url}
                    </p>
                  )}
                </div>
                <span
                  className={`flex-shrink-0 px-2 py-0.5 rounded text-xs ${
                    STATUS_COLOR[item.status] ||
                    "text-zinc-400 bg-zinc-800/50"
                  }`}
                >
                  {item.status.replace("_", " ")}
                </span>
                <time className="flex-shrink-0 text-xs text-zinc-600 w-16 text-right">
                  {timeAgo(item.created_at)}
                </time>
              </button>
            </li>
          );
        })}
      </ul>
    );
  }, [items, loading, error, handleClick]);

  return (
    <div className="w-full max-w-2xl bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-zinc-400" />
          <h3 className="text-sm font-medium text-zinc-300">Recent Research</h3>
        </div>
        <button
          onClick={load}
          className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          Refresh
        </button>
      </div>
      {content}
    </div>
  );
});

export default HistoryList;
