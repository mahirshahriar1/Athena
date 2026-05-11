"use client";

import { useCallback, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAppDispatch, useAppSelector } from "@/lib/store";
import { approvePlan, fetchReport, reset } from "@/lib/slices/researchSlice";
import { useResearchStream } from "@/hooks/useResearchStream";
import { usePolling } from "@/hooks/usePolling";
import PlanApproval from "@/components/PlanApproval";
import AgentTimeline from "@/components/AgentTimeline";
import ReportViewer from "@/components/ReportViewer";
import StatusBadge from "@/components/StatusBadge";
import { ArrowLeft } from "lucide-react";

export default function ResearchPage() {
  const params = useParams();
  const router = useRouter();
  const dispatch = useAppDispatch();

  const jobId = params.jobId as string;
  const { status, plan, company, events, currentNode, report, error } =
    useAppSelector((state) => state.research);

  // WebSocket streaming when running
  const shouldStream = useMemo(
    () => status === "running",
    [status]
  );
  const { isConnected } = useResearchStream({
    jobId,
    enabled: shouldStream,
  });

  // Poll for completion
  usePolling({
    jobId,
    enabled: status === "running",
    interval: 5000,
  });

  // Fetch report once completed
  useEffect(() => {
    if (status === "completed" && !report) {
      dispatch(fetchReport(jobId));
    }
  }, [status, report, jobId, dispatch]);

  const handleApprove = useCallback(async () => {
    await dispatch(approvePlan(jobId));
  }, [dispatch, jobId]);

  const handleReject = useCallback(() => {
    dispatch(reset());
    router.push("/");
  }, [dispatch, router]);

  const handleBack = useCallback(() => {
    dispatch(reset());
    router.push("/");
  }, [dispatch, router]);

  const showTimeline = useMemo(
    () => status === "running" || status === "completed",
    [status]
  );

  return (
    <div className="min-h-screen px-4 py-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="flex items-center gap-3">
          {isConnected && (
            <span className="flex items-center gap-1.5 text-xs text-green-400">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              Live
            </span>
          )}
          <StatusBadge status={status} />
        </div>
      </div>

      {/* Company name */}
      {company && (
        <h1 className="text-3xl font-bold text-white mb-6">
          Researching: <span className="text-blue-400">{company}</span>
        </h1>
      )}

      {/* Error */}
      {error && (
        <div className="mb-6 px-4 py-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Plan Approval */}
      {status === "awaiting_approval" && plan.length > 0 && (
        <div className="flex justify-center mb-8">
          <PlanApproval
            plan={plan}
            company={company}
            onApprove={handleApprove}
            onReject={handleReject}
            isLoading={status === "running"}
          />
        </div>
      )}

      {/* Agent Timeline */}
      {showTimeline && (
        <div className="flex justify-center mb-8">
          <AgentTimeline events={events} currentNode={currentNode} />
        </div>
      )}

      {/* Final Report */}
      {report && (
        <div className="flex justify-center">
          <ReportViewer report={report} company={company} />
        </div>
      )}
    </div>
  );
}
