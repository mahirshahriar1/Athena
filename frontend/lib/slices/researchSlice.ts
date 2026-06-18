import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";

// --- Types ---

export interface TimelineEvent {
  id: string;
  type: "node_start" | "node_done" | "token" | "error" | "complete";
  node: string;
  content?: string;
  timestamp: string;
}

export interface TokenUsage {
  input: number;
  output: number;
  total: number;
  calls: number;
}

export interface ResearchState {
  jobId: string | null;
  company: string;
  plan: string[];
  status: "idle" | "planning" | "awaiting_approval" | "running" | "completed" | "error";
  events: TimelineEvent[];
  currentNode: string | null;
  report: string | null;
  tokens: TokenUsage | null;
  error: string | null;
}

const initialState: ResearchState = {
  jobId: null,
  company: "",
  plan: [],
  status: "idle",
  events: [],
  currentNode: null,
  report: null,
  tokens: null,
  error: null,
};

// --- Async Thunks ---

export interface StartResearchArgs {
  company: string;
  websiteUrl?: string;
}

export const startResearch = createAsyncThunk(
  "research/start",
  async (args: StartResearchArgs, { rejectWithValue }) => {
    try {
      const res = await fetch("/api/research/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company: args.company,
          website_url: args.websiteUrl || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        return rejectWithValue(err.detail || "Failed to start research");
      }

      return await res.json();
    } catch (err) {
      return rejectWithValue("Network error: Could not reach backend");
    }
  }
);

export const approvePlan = createAsyncThunk(
  "research/approve",
  async (jobId: string, { rejectWithValue }) => {
    try {
      const res = await fetch(`/api/research/${jobId}/approve`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json();
        return rejectWithValue(err.detail || "Failed to approve plan");
      }

      return await res.json();
    } catch (err) {
      return rejectWithValue("Network error: Could not reach backend");
    }
  }
);

export const fetchReport = createAsyncThunk(
  "research/fetchReport",
  async (jobId: string, { rejectWithValue }) => {
    try {
      const res = await fetch(`/api/research/${jobId}/report`);

      if (!res.ok) {
        const err = await res.json();
        return rejectWithValue(err.detail || "Failed to fetch report");
      }

      return await res.json();
    } catch (err) {
      return rejectWithValue("Network error: Could not reach backend");
    }
  }
);

// --- Slice ---

const researchSlice = createSlice({
  name: "research",
  initialState,
  reducers: {
    setCompany(state, action: PayloadAction<string>) {
      state.company = action.payload;
    },
    addEvent(state, action: PayloadAction<TimelineEvent>) {
      state.events.push(action.payload);
    },
    setCurrentNode(state, action: PayloadAction<string | null>) {
      state.currentNode = action.payload;
    },
    setStatus(state, action: PayloadAction<ResearchState["status"]>) {
      state.status = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
      if (action.payload) {
        state.status = "error";
      }
    },
    setTokens(state, action: PayloadAction<TokenUsage>) {
      state.tokens = action.payload;
    },
    reset() {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    // Start research
    builder.addCase(startResearch.pending, (state) => {
      state.status = "planning";
      state.error = null;
    });
    builder.addCase(startResearch.fulfilled, (state, action) => {
      state.jobId = action.payload.job_id;
      state.plan = action.payload.plan;
      state.status = "awaiting_approval";
    });
    builder.addCase(startResearch.rejected, (state, action) => {
      state.status = "error";
      state.error = action.payload as string;
    });

    // Approve plan — backend returns immediately after marking approval.
    // The WebSocket drives execution and emits "complete" when the writer
    // finishes, which is what flips status to "completed".
    builder.addCase(approvePlan.pending, (state) => {
      state.status = "running";
    });
    builder.addCase(approvePlan.fulfilled, (state) => {
      state.status = "running";
    });
    builder.addCase(approvePlan.rejected, (state, action) => {
      state.status = "error";
      state.error = action.payload as string;
    });

    // Fetch report
    builder.addCase(fetchReport.fulfilled, (state, action) => {
      state.report = action.payload.report;
      if (action.payload.tokens) {
        state.tokens = action.payload.tokens;
      }
      if (action.payload.report) {
        state.status = "completed";
      }
    });
    builder.addCase(fetchReport.rejected, (state, action) => {
      state.error = action.payload as string;
    });
  },
});

export const { setCompany, addEvent, setCurrentNode, setStatus, setError, setTokens, reset } =
  researchSlice.actions;

export default researchSlice.reducer;
