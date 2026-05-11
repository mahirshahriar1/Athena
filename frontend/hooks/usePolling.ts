"use client";

import { useCallback, useEffect, useRef } from "react";
import { useAppDispatch } from "@/lib/store";
import { fetchReport, setStatus } from "@/lib/slices/researchSlice";

interface UsePollingOptions {
  jobId: string | null;
  interval?: number;
  enabled: boolean;
}

export function usePolling({ jobId, interval = 3000, enabled }: UsePollingOptions) {
  const dispatch = useAppDispatch();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const poll = useCallback(async () => {
    if (!jobId) return;

    try {
      const res = await fetch(`/api/research/${jobId}/status`);
      if (!res.ok) return;

      const data = await res.json();

      if (data.status === "completed") {
        dispatch(setStatus("completed"));
        dispatch(fetchReport(jobId));
        // Stop polling once completed
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err) {
      console.error("Polling error:", err);
    }
  }, [jobId, dispatch]);

  useEffect(() => {
    if (!enabled || !jobId) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, jobId, interval, poll]);
}
