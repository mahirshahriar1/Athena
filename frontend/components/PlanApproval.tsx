"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  CheckCircle,
  XCircle,
  ListChecks,
  Plus,
  Trash2,
  GripVertical,
  RefreshCw,
  Loader2,
} from "lucide-react";

// Mirror the backend constants in backend/api/routes.py
const PLAN_MAX_TASKS = 8;
const PLAN_MIN_TASKS = 1;
const TASK_MIN_CHARS = 2;
const TASK_MAX_CHARS = 200;

interface PlanApprovalProps {
  plan: string[];
  company: string;
  onApprove: (editedPlan: string[]) => void;
  onReject: () => void;
  onRegenerate: () => Promise<void> | void;
  isLoading: boolean;
}

interface DraftTask {
  id: string;
  text: string;
}

let nextId = 1;
const newTask = (text = ""): DraftTask => ({
  id: `task-${Date.now()}-${nextId++}`,
  text,
});

const PlanApproval = React.memo(function PlanApproval({
  plan,
  company,
  onApprove,
  onReject,
  onRegenerate,
  isLoading,
}: PlanApprovalProps) {
  const [tasks, setTasks] = useState<DraftTask[]>(() =>
    plan.map((t) => newTask(t))
  );
  const [regenerating, setRegenerating] = useState(false);
  const dragIndexRef = useRef<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  // Sync external plan changes (e.g. after regenerate) into local draft.
  // We replace whenever the serialized plans differ to avoid clobbering
  // mid-edit when nothing has actually changed.
  const planKey = useMemo(() => plan.join(""), [plan]);
  const tasksKey = useMemo(() => tasks.map((t) => t.text).join(""), [tasks]);
  useEffect(() => {
    if (planKey !== tasksKey) {
      setTasks(plan.map((t) => newTask(t)));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [planKey]);

  const validation = useMemo(() => {
    const cleaned = tasks.map((t) => t.text.trim()).filter(Boolean);
    if (cleaned.length < PLAN_MIN_TASKS) {
      return { ok: false, reason: `At least ${PLAN_MIN_TASKS} task required.` };
    }
    if (cleaned.length > PLAN_MAX_TASKS) {
      return { ok: false, reason: `At most ${PLAN_MAX_TASKS} tasks.` };
    }
    for (let i = 0; i < cleaned.length; i++) {
      if (cleaned[i].length < TASK_MIN_CHARS) {
        return { ok: false, reason: `Task ${i + 1} is too short.` };
      }
      if (cleaned[i].length > TASK_MAX_CHARS) {
        return {
          ok: false,
          reason: `Task ${i + 1} is over ${TASK_MAX_CHARS} chars.`,
        };
      }
    }
    return { ok: true as const, reason: null, cleaned };
  }, [tasks]);

  const handleTextChange = useCallback(
    (id: string, value: string) => {
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, text: value } : t))
      );
    },
    []
  );

  const handleDelete = useCallback((id: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const handleAdd = useCallback(() => {
    setTasks((prev) => {
      if (prev.length >= PLAN_MAX_TASKS) return prev;
      return [...prev, newTask("")];
    });
  }, []);

  const handleDragStart = useCallback(
    (e: React.DragEvent<HTMLLIElement>, index: number) => {
      dragIndexRef.current = index;
      e.dataTransfer.effectAllowed = "move";
    },
    []
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLLIElement>, index: number) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOverIndex(index);
    },
    []
  );

  const handleDragLeave = useCallback(() => {
    setDragOverIndex(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLLIElement>, dropIndex: number) => {
      e.preventDefault();
      const from = dragIndexRef.current;
      dragIndexRef.current = null;
      setDragOverIndex(null);
      if (from === null || from === dropIndex) return;
      setTasks((prev) => {
        const next = [...prev];
        const [moved] = next.splice(from, 1);
        next.splice(dropIndex, 0, moved);
        return next;
      });
    },
    []
  );

  const handleApprove = useCallback(() => {
    if (!validation.ok || isLoading) return;
    onApprove(validation.cleaned ?? []);
  }, [validation, isLoading, onApprove]);

  const handleReject = useCallback(() => {
    if (!isLoading) onReject();
  }, [isLoading, onReject]);

  const handleRegenerate = useCallback(async () => {
    if (regenerating || isLoading) return;
    setRegenerating(true);
    try {
      await onRegenerate();
    } finally {
      setRegenerating(false);
    }
  }, [regenerating, isLoading, onRegenerate]);

  const atMaxTasks = tasks.length >= PLAN_MAX_TASKS;

  return (
    <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <ListChecks className="w-6 h-6 text-blue-400" />
          <h2 className="text-xl font-semibold text-white">
            Research Plan for{" "}
            <span className="text-blue-400">{company}</span>
          </h2>
        </div>
        <button
          onClick={handleRegenerate}
          disabled={regenerating || isLoading}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md
                     bg-zinc-800 text-zinc-300 text-xs hover:bg-zinc-700
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors duration-200"
          title="Re-run the planner with the same company + seed URL"
        >
          {regenerating ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <RefreshCw className="w-3.5 h-3.5" />
          )}
          Regenerate
        </button>
      </div>

      <p className="text-zinc-400 text-sm mb-4">
        Review and edit before running. Drag <GripVertical className="inline w-3 h-3" /> to reorder, click text to edit, or remove individual tasks.
      </p>

      <ul className="space-y-2 mb-3">
        {tasks.map((task, i) => {
          const isDragOver = dragOverIndex === i;
          return (
            <li
              key={task.id}
              draggable={!isLoading}
              onDragStart={(e) => handleDragStart(e, i)}
              onDragOver={(e) => handleDragOver(e, i)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, i)}
              className={`flex items-start gap-2 p-2 rounded-lg border transition-colors
                          ${
                            isDragOver
                              ? "border-blue-500 bg-blue-500/5"
                              : "border-zinc-700/50 bg-zinc-800/50"
                          }`}
            >
              <span
                className="flex-shrink-0 mt-1.5 cursor-grab active:cursor-grabbing text-zinc-500 hover:text-zinc-300"
                title="Drag to reorder"
              >
                <GripVertical className="w-4 h-4" />
              </span>
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600/20 text-blue-400
                             flex items-center justify-center text-xs font-medium mt-0.5">
                {i + 1}
              </span>
              <input
                type="text"
                value={task.text}
                onChange={(e) => handleTextChange(task.id, e.target.value)}
                disabled={isLoading}
                maxLength={TASK_MAX_CHARS}
                placeholder="Describe a research task…"
                className="flex-1 bg-transparent text-zinc-200 text-sm
                           border-0 border-b border-transparent
                           focus:outline-none focus:border-blue-500/50
                           disabled:opacity-50
                           transition-colors"
              />
              <button
                onClick={() => handleDelete(task.id)}
                disabled={isLoading || tasks.length <= PLAN_MIN_TASKS}
                className="flex-shrink-0 p-1 text-zinc-500 hover:text-red-400
                           disabled:opacity-30 disabled:cursor-not-allowed
                           transition-colors"
                title={
                  tasks.length <= PLAN_MIN_TASKS
                    ? "At least one task required"
                    : "Remove task"
                }
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </li>
          );
        })}
      </ul>

      <button
        onClick={handleAdd}
        disabled={atMaxTasks || isLoading}
        className="w-full flex items-center justify-center gap-2 px-3 py-2 mb-4 rounded-lg
                   border border-dashed border-zinc-700 text-zinc-400 text-sm
                   hover:border-zinc-500 hover:text-zinc-200
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors duration-200"
      >
        <Plus className="w-4 h-4" />
        {atMaxTasks
          ? `Maximum of ${PLAN_MAX_TASKS} tasks reached`
          : "Add a research task"}
      </button>

      {!validation.ok && (
        <p className="mb-3 px-3 py-2 rounded-md bg-amber-900/20 border border-amber-700/30 text-amber-300 text-xs">
          {validation.reason}
        </p>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleApprove}
          disabled={!validation.ok || isLoading}
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
