"use client";

import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { Bot, CheckCircle, AlertCircle, Zap } from "lucide-react";
import { TimelineEvent } from "@/lib/slices/researchSlice";

interface AgentTimelineProps {
  events: TimelineEvent[];
  currentNode: string | null;
}

const NODE_LABELS: Record<string, string> = {
  planner: "Planner Agent",
  scraper_dispatch: "Scraper Dispatch",
  scraper_worker: "Scraper Agent",
  rag_ingest: "RAG Ingestion",
  analyst_dispatch: "Analyst Dispatch",
  analyst_worker: "Analyst Agent",
  critic: "Critic Agent",
  writer: "Writer Agent",
};

const AgentTimeline = React.memo(function AgentTimeline({
  events,
  currentNode,
}: AgentTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Filter to only meaningful events (node_start, node_done, error)
  const displayEvents = useMemo(
    () => events.filter((e) => e.type !== "token"),
    [events]
  );

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [displayEvents.length, scrollToBottom]);

  const getEventIcon = useCallback((type: string) => {
    switch (type) {
      case "node_start":
        return <Zap className="w-4 h-4 text-blue-400" />;
      case "node_done":
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Bot className="w-4 h-4 text-zinc-400" />;
    }
  }, []);

  return (
    <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-700 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-zinc-700 flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-300">Agent Timeline</h3>
        {currentNode && (
          <span className="flex items-center gap-2 text-xs text-blue-400">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            {NODE_LABELS[currentNode] || currentNode}
          </span>
        )}
      </div>

      <div
        ref={scrollRef}
        className="max-h-80 overflow-y-auto scrollbar-thin p-4 space-y-2"
      >
        {displayEvents.length === 0 ? (
          <p className="text-zinc-500 text-sm text-center py-8">
            Waiting for agent activity...
          </p>
        ) : (
          displayEvents.map((event) => (
            <div
              key={event.id}
              className="flex items-start gap-3 p-2 rounded-lg hover:bg-zinc-800/50
                         transition-colors duration-150 animate-in fade-in"
            >
              <div className="flex-shrink-0 mt-0.5">{getEventIcon(event.type)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-zinc-200">
                  <span className="font-medium">
                    {NODE_LABELS[event.node] || event.node}
                  </span>
                  <span className="text-zinc-500 ml-2">
                    {event.type === "node_start" ? "started" : ""}
                    {event.type === "node_done" ? "completed" : ""}
                    {event.type === "error" ? "failed" : ""}
                  </span>
                </p>
                {event.content && (
                  <p className="text-xs text-zinc-500 mt-0.5 truncate">
                    {event.content}
                  </p>
                )}
              </div>
              <time className="flex-shrink-0 text-xs text-zinc-600">
                {new Date(event.timestamp).toLocaleTimeString()}
              </time>
            </div>
          ))
        )}
      </div>
    </div>
  );
});

export default AgentTimeline;
