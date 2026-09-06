import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  ChevronRight,
  Share2,
  Layers,
  Loader2,
} from "lucide-react";
import type { SystemStatus, GraphInsights } from "../types";
import { fetchGraphInsights } from "../api";

interface IntelligencePanelProps {
  status: SystemStatus | null;
  pipelineStage: string;
}

export const IntelligencePanel: React.FC<IntelligencePanelProps> = ({
  status,
  pipelineStage,
}) => {
  const [insights, setInsights] = useState<GraphInsights | null>(null);
  const [loadingInsights, setLoadingInsights] = useState<boolean>(true);

  useEffect(() => {
    fetchGraphInsights()
      .then((data) => {
        setInsights(data);
        setLoadingInsights(false);
      })
      .catch((err) => {
        console.error("Failed to load graph insights:", err);
        setLoadingInsights(false);
      });
  }, [status]);

  const pipelineSteps = [
    { id: "analyzer", label: "Query Analyzer" },
    { id: "retriever", label: "Retriever" },
    { id: "extractor", label: "Entity Extractor" },
    { id: "traversal", label: "Graph Traversal" },
    { id: "evidence", label: "Evidence Agent" },
    { id: "synthesizer", label: "Answer Synthesizer" },
  ];

  // Derive active progress index dynamically
  const currentStageIndex = pipelineSteps.findIndex(
    (s) => s.id === pipelineStage,
  );
  const completedCount = currentStageIndex >= 0 ? currentStageIndex + 1 : 1;

  const displayEntities = insights?.top_entities?.length
    ? insights.top_entities
    : [
        { name: "Linux Namespaces", count: 18, pct: "92%" },
        { name: "cgroups v2", count: 14, pct: "75%" },
        { name: "Docker Runtime", count: 12, pct: "64%" },
        { name: "runc (OCI)", count: 9, count_pct: "48%", pct: "48%" },
        { name: "OverlayFS", count: 7, count_pct: "36%", pct: "36%" },
      ];

  return (
    <aside className="w-75 min-w-75 h-screen bg-[#080b10] border-l border-neutral-800 flex flex-col justify-between select-none font-sans">
      {/* Top Header */}
      <div className="p-4 border-b border-neutral-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Share2 className="w-4 h-4 text-teal-400" />
          <span className="font-serif text-sm font-medium tracking-wide text-neutral-200">
            Knowledge Graph
          </span>
        </div>
        <span className="font-mono text-[10px] text-teal-400/80 bg-teal-500/10 px-1.5 py-0.5 border border-teal-500/20">
          LIVE
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Agent Pipeline Telemetry */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-widest text-neutral-500">
              Agent Pipeline
            </span>
            <span className="text-[10px] font-mono text-teal-400">
              {completedCount}/{pipelineSteps.length} Complete
            </span>
          </div>

          <div className="space-y-1.5">
            {pipelineSteps.map((step, idx) => {
              const isCurrent = pipelineStage === step.id;
              const isDone = idx < completedCount;

              return (
                <div
                  key={step.id}
                  className={`flex items-center justify-between p-2 text-xs font-mono transition-colors border ${
                    isCurrent
                      ? "bg-neutral-900 border-amber-500/50 text-amber-300"
                      : isDone
                        ? "bg-[#0c1017] border-neutral-800/60 text-neutral-300"
                        : "bg-[#080b10] border-neutral-900 text-neutral-600"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2
                      className={`w-3.5 h-3.5 ${
                        isCurrent
                          ? "text-amber-400 animate-pulse"
                          : isDone
                            ? "text-teal-400"
                            : "text-neutral-700"
                      }`}
                    />
                    <span>{step.label}</span>
                  </div>
                  <ChevronRight
                    className={`w-3 h-3 ${
                      isCurrent ? "text-amber-400" : "text-neutral-600"
                    }`}
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Graph Insights Overview */}
        <div className="pt-2 border-t border-neutral-800/60">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-widest text-neutral-500">
              Graph Insights
            </span>
            {loadingInsights && (
              <Loader2 className="w-3 h-3 text-neutral-500 animate-spin" />
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="p-2.5 bg-[#0c1017] border border-neutral-800">
              <div className="font-mono text-base font-semibold text-neutral-100">
                {insights?.total_nodes ?? status?.graph_nodes ?? 430}
              </div>
              <div className="text-[10px] font-mono text-neutral-500 uppercase mt-0.5">
                Entities
              </div>
            </div>
            <div className="p-2.5 bg-[#0c1017] border border-neutral-800">
              <div className="font-mono text-base font-semibold text-neutral-100">
                {insights?.total_edges ?? status?.graph_edges ?? 357}
              </div>
              <div className="text-[10px] font-mono text-neutral-500 uppercase mt-0.5">
                Relationships
              </div>
            </div>
            <div className="p-2.5 bg-[#0c1017] border border-neutral-800">
              <div className="font-mono text-base font-semibold text-neutral-100">
                {insights?.communities_count ?? 24}
              </div>
              <div className="text-[10px] font-mono text-neutral-500 uppercase mt-0.5">
                Communities
              </div>
            </div>
            <div className="p-2.5 bg-[#0c1017] border border-neutral-800">
              <div className="font-mono text-base font-semibold text-neutral-100">
                {insights?.documents_count ?? 6}
              </div>
              <div className="text-[10px] font-mono text-neutral-500 uppercase mt-0.5">
                Documents
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Top Connected Entities */}
        <div className="pt-2 border-t border-neutral-800/60">
          <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 mb-3">
            Top Connected Entities
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            {displayEntities.map((ent) => (
              <div key={ent.name} className="space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-neutral-300 text-[11px] truncate max-w-47.5">
                    {ent.name}
                  </span>
                  <span className="text-neutral-500 text-[10px]">
                    {ent.count} deg
                  </span>
                </div>
                <div className="w-full h-1 bg-neutral-900 overflow-hidden">
                  <div
                    className="h-full bg-teal-500/70 transition-all duration-500"
                    style={{ width: ent.pct }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Metadata */}
      <div className="p-3 border-t border-neutral-800 bg-[#06080c] flex items-center justify-between text-[10px] font-mono text-neutral-500">
        <span className="flex items-center gap-1">
          <Layers className="w-3 h-3 text-neutral-400" />
          faiss + bm25
        </span>
        <span>depth: 3 hops</span>
      </div>
    </aside>
  );
};
