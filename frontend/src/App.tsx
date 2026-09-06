import { useState, useEffect, useCallback } from "react";
import {
  Search,
  ChevronRight,
  ExternalLink,
  Cpu,
  Clock,
  Layers,
  FileCheck2,
  XCircle,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { Sidebar } from "./components/Sidebar";
import { IntelligencePanel } from "./components/IntelligencePanel";
import { GraphCanvas } from "./components/GraphCanvas";
import { FormattedAnswer } from "./components/FormattedAnswer";
import { Views } from "./components/Views";
import { fetchSystemStatus, runQuery } from "./api";
import type { SystemStatus, QueryResponse } from "./types";

type AppQueryResponse = QueryResponse & {
  evidence_chunks?: Array<{
    chunk_id: string;
    text: string;
    doc_id: string;
    score: number;
  }>;
};

export default function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [activeView, setActiveView] = useState("research");
  const [queryInput, setQueryInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [queryCount, setQueryCount] = useState(0);
  const [pipelineStage, setPipelineStage] = useState("idle");
  const [response, setResponse] = useState<AppQueryResponse | null>(null);
  const [history, setHistory] = useState<
    Array<{ query: string; timestamp: string }>
  >([]);

  const handleExecute = useCallback(
    async (promptToRun?: string) => {
      const q = promptToRun !== undefined ? promptToRun : queryInput;
      if (!q.trim()) return;

      setLoading(true);
      setPipelineStage("analyzer");

      try {
        setTimeout(() => setPipelineStage("retriever"), 150);
        setTimeout(() => setPipelineStage("extractor"), 350);
        setTimeout(() => setPipelineStage("traversal"), 600);
        setTimeout(() => setPipelineStage("evidence"), 850);
        setTimeout(() => setPipelineStage("synthesizer"), 1100);

        const result = await runQuery(q, 3, 1);
        setResponse(result);
        setQueryCount((prev) => prev + 1);

        const now = new Date().toTimeString().slice(0, 8);
        setHistory((prev) => [{ query: q, timestamp: now }, ...prev]);
      } catch (err) {
        console.error("Execution failed:", err);
      } finally {
        setLoading(false);
      }
    },
    [queryInput],
  );

  useEffect(() => {
    fetchSystemStatus()
      .then((data) => setStatus(data))
      .catch((err) => console.error("Failed to fetch initial status:", err));

    setTimeout(() => {
      void handleExecute(queryInput);
    }, 0);
  }, [handleExecute, queryInput]);

  const handleClear = () => {
    setQueryInput("");
    setResponse(null);
  };

  const handleNewSession = () => {
    setQueryInput("");
    setResponse(null);
    setQueryCount(0);
    setActiveView("research");
  };

  const handleRefreshGraph = async () => {
    try {
      const data = await fetchSystemStatus();
      setStatus(data);

      if (queryInput.trim()) {
        handleExecute(queryInput);
      }
    } catch (err) {
      console.error("Failed to refresh status:", err);
    }
  };

  const handleSelectHistory = (queryText: string) => {
    setQueryInput(queryText);
    setActiveView("research");
    handleExecute(queryText);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#06080c] text-neutral-200 antialiased font-sans select-none">
      {/* 1. Left Fixed Navigation */}
      <Sidebar
        status={status}
        activeView={activeView}
        setActiveView={setActiveView}
        queryCount={queryCount}
        onRefreshGraph={handleRefreshGraph}
        onNewSession={handleNewSession}
      />

      {/* 2. Main Workstation Body */}
      <main className="flex-1 h-screen overflow-y-auto flex flex-col bg-[#070a0f] border-r border-neutral-800">
        {activeView !== "research" ? (
          <Views
            activeView={activeView}
            status={status}
            history={history}
            onSelectHistory={handleSelectHistory}
            response={response}
          />
        ) : (
          <>
            {/* Search Header */}
            <header className="p-5 border-b border-neutral-800/80 bg-[#080b11] sticky top-0 z-20">
              <div className="max-w-4xl space-y-3">
                <div className="relative flex items-center">
                  <Search className="w-4 h-4 text-teal-400/80 absolute left-3.5 top-3.5" />
                  <textarea
                    rows={2}
                    value={queryInput}
                    onChange={(e) => setQueryInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleExecute();
                      }
                    }}
                    placeholder="Enter query (e.g., How do Linux namespaces isolate container processes?)..."
                    className="w-full bg-[#0c1017] border border-neutral-800 pl-10 pr-24 py-2.5 text-xs font-mono text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-teal-500/70 transition-colors resize-none leading-relaxed"
                  />
                  <div className="absolute right-2.5 top-2.5 flex items-center gap-1">
                    {queryInput && (
                      <button
                        onClick={handleClear}
                        title="Clear query and answer"
                        className="p-1 text-neutral-500 hover:text-rose-400 transition-colors cursor-pointer"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleExecute()}
                      disabled={loading || !queryInput.trim()}
                      className="px-4 py-1.5 bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 border border-teal-500/40 text-xs font-mono font-medium transition-colors disabled:opacity-40 flex items-center gap-1.5 cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{loading ? "REASONING..." : "EXECUTE QUERY"}</span>
                    </button>
                    {response && (
                      <button
                        onClick={handleClear}
                        className="px-3 py-1.5 bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-200 text-xs font-mono flex items-center gap-1.5 cursor-pointer"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>RESET</span>
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] font-mono text-neutral-500">
                    <span>ENTER to query</span>
                    <span>•</span>
                    <span>SHIFT+ENTER for newline</span>
                  </div>
                </div>
              </div>
            </header>

            {/* Session Canvas */}
            <div className="p-6 max-w-5xl space-y-6">
              <section className="space-y-3">
                <div className="text-[10px] font-mono text-teal-400/90 uppercase tracking-widest flex items-center gap-1.5">
                  <span>RESEARCH SESSION</span>
                  <ChevronRight className="w-3 h-3 text-neutral-600" />
                  <span className="text-neutral-400">CORPUS: ACTIVE</span>
                </div>
                <h1 className="font-serif text-2xl font-normal text-neutral-100 tracking-tight leading-snug">
                  {response?.query || queryInput || "No Active Query"}
                </h1>

                {response && (
                  <div className="flex items-center gap-6 pt-1 text-[11px] font-mono text-neutral-400 border-b border-neutral-800/80 pb-3">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-neutral-500" />
                      <span>LATENCY: {response.latency}s</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-neutral-500" />
                      <span>MODEL: GEMINI 3.5 FLASH-LITE</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-neutral-500" />
                      <span>TRAVERSAL: {response.traversal_depth} HOPS</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <FileCheck2 className="w-3.5 h-3.5 text-neutral-500" />
                      <span>
                        CITATIONS: {response.cited_chunk_ids?.length ?? 0}
                      </span>
                    </div>
                  </div>
                )}
              </section>

              {/* Synthesized Output */}
              <section className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-neutral-500">
                    SYNTHESIZED ARCHITECTURAL VERDICT
                  </div>
                  {response?.answer && (
                    <button
                      onClick={() => setResponse(null)}
                      className="text-[10px] font-mono text-neutral-500 hover:text-neutral-300"
                    >
                      Clear Answer
                    </button>
                  )}
                </div>

                <div className="p-5 bg-[#090d14] border border-neutral-800">
                  {response?.answer ? (
                    <FormattedAnswer content={response.answer} />
                  ) : (
                    <div className="text-neutral-500 font-mono text-xs py-4 text-center">
                      Ready. Submit a prompt above or pick a query from Query
                      History.
                    </div>
                  )}
                </div>
              </section>

              {/* Interactive Topological Graph */}
              <section className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-neutral-400">
                    TOPOLOGICAL REASONING GRAPH
                  </div>
                  <div className="text-[10px] font-mono text-neutral-500">
                    INTERACTIVE CANVAS
                  </div>
                </div>
                <div className="w-full h-105 relative border border-neutral-800 bg-[#07090e]">
                  <GraphCanvas
                    nodesData={response?.subgraph?.nodes}
                    edgesData={response?.subgraph?.edges}
                  />
                </div>
              </section>

              {/* Dynamic Retrieved Evidence Chunks */}
              <section className="space-y-3 pt-6 pb-12">
                <div className="text-[10px] font-mono uppercase tracking-wider text-neutral-400">
                  PRIMARY EVIDENCE CHUNKS & SOURCE PROVENANCE
                </div>

                {response?.evidence_chunks &&
                response.evidence_chunks.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {response.evidence_chunks.map((chunk, idx) => (
                      <div
                        key={`${chunk.chunk_id}-${idx}`}
                        className="p-3.5 bg-[#090d14] border border-neutral-800/80 space-y-2 hover:border-neutral-700 transition-colors select-text"
                      >
                        <div className="flex items-center justify-between text-[11px] font-mono">
                          <span className="text-teal-400 font-medium truncate">
                            {chunk.chunk_id}
                          </span>
                          <ExternalLink className="w-3 h-3 text-neutral-500" />
                        </div>
                        <p className="text-[11px] text-neutral-300 font-mono leading-relaxed line-clamp-4">
                          {chunk.text}
                        </p>
                        <div className="text-[10px] font-mono text-neutral-500 pt-1 border-t border-neutral-900 flex justify-between">
                          <span className="truncate max-w-50">
                            DOC: {chunk.doc_id}
                          </span>
                          <span>SCORE: {chunk.score.toFixed(2)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-[#090d14] border border-neutral-800 text-neutral-500 font-mono text-xs">
                    {response
                      ? "No explicit evidence chunks returned for this query."
                      : "Awaiting query execution."}
                  </div>
                )}
              </section>
            </div>
          </>
        )}
      </main>

      {/* 3. Right Intelligence Panel */}
      <IntelligencePanel status={status} pipelineStage={pipelineStage} />
    </div>
  );
}
