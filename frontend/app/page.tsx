"use client";

import { useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAppDispatch, useAppSelector } from "@/lib/store";
import { startResearch, setCompany } from "@/lib/slices/researchSlice";
import CompanyInput from "@/components/CompanyInput";
import StatusBadge from "@/components/StatusBadge";
import { Brain, Zap, Shield, Clock } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { status, error, jobId } = useAppSelector((state) => state.research);

  const isLoading = useMemo(
    () => status === "planning",
    [status]
  );

  const handleSubmit = useCallback(
    async (company: string) => {
      dispatch(setCompany(company));
      const result = await dispatch(startResearch(company));

      if (startResearch.fulfilled.match(result)) {
        router.push(`/research/${result.payload.job_id}`);
      }
    },
    [dispatch, router]
  );

  const features = useMemo(
    () => [
      {
        icon: Brain,
        title: "Multi-Agent AI",
        desc: "8 specialized agents work in parallel",
      },
      {
        icon: Zap,
        title: "Real-time Streaming",
        desc: "Watch agents work via WebSocket",
      },
      {
        icon: Shield,
        title: "Quality Control",
        desc: "Critic agent ensures report quality",
      },
      {
        icon: Clock,
        title: "Human-in-the-Loop",
        desc: "Approve the plan before execution",
      },
    ],
    []
  );

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-white mb-4 tracking-tight">
          Athena
        </h1>
        <p className="text-xl text-zinc-400 max-w-lg mx-auto">
          Autonomous competitive intelligence. Enter a company name and get a
          full analysis powered by AI agents.
        </p>
      </div>

      {/* Input */}
      <CompanyInput onSubmit={handleSubmit} isLoading={isLoading} />

      {/* Error display */}
      {error && (
        <div className="mt-4 px-4 py-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm max-w-xl">
          {error}
        </div>
      )}

      {/* Status */}
      {status !== "idle" && (
        <div className="mt-4">
          <StatusBadge status={status} />
        </div>
      )}

      {/* Features grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-16 max-w-2xl w-full">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700
                       transition-colors duration-200"
          >
            <feature.icon className="w-8 h-8 text-blue-500 mb-3" />
            <h3 className="text-white font-medium mb-1">{feature.title}</h3>
            <p className="text-zinc-500 text-sm">{feature.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
