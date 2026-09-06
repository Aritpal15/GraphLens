import React from "react";
import { GraphCanvas } from "./GraphCanvas";
import { FileText, Boxes, History, ArrowUpRight } from "lucide-react";
import type { SystemStatus, QueryResponse } from "../types";

interface ViewsProps {
  activeView: string;
  status: SystemStatus | null;
  history: Array<{ query: string; timestamp: string }>;
  onSelectHistory: (query: string) => void;
  response: QueryResponse | null;
}

export const Views: React.FC<ViewsProps> = ({
  activeView,
  status,
  history,
  onSelectHistory,
  response,
}) => {
  if (activeView === "graph") {
    return (
      <div className="p-6 space-y-4 h-[calc(100vh-80px)] flex flex-col">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-mono text-neutral-100 font-semibold uppercase">
              Full Knowledge Graph
            </h2>
            <p className="text-xs font-mono text-neutral-500 mt-1">
              Visualizing {status?.graph_nodes ?? 430} entity nodes and{" "}
              {status?.graph_edges ?? 357} relational edges.
            </p>
          </div>
        </div>
        <div className="flex-1 border border-neutral-800 bg-[#080b10]">
          <GraphCanvas
            nodesData={response?.subgraph?.nodes}
            edgesData={response?.subgraph?.edges}
          />
        </div>
      </div>
    );
  }

  if (activeView === "documents") {
    const docs = [
      {
        id: "01_docker_internals.pdf",
        chunks: 22,
        size: "1.4 MB",
        date: "2026-09-01",
      },
      {
        id: "02_linux_kernel_cgroups.pdf",
        chunks: 18,
        size: "890 KB",
        date: "2026-09-01",
      },
      {
        id: "03_oci_runtime_spec.pdf",
        chunks: 14,
        size: "620 KB",
        date: "2026-09-02",
      },
      {
        id: "04_containerd_architecture.pdf",
        chunks: 16,
        size: "1.1 MB",
        date: "2026-09-03",
      },
      {
        id: "05_kubernetes_networking.pdf",
        chunks: 10,
        size: "750 KB",
        date: "2026-09-03",
      },
      {
        id: "06_ebpf_isolation_primitives.pdf",
        chunks: 6,
        size: "430 KB",
        date: "2026-09-04",
      },
    ];

    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <div>
          <h2 className="text-xl font-mono text-neutral-100 font-semibold uppercase">
            Indexed Documents
          </h2>
          <p className="text-xs font-mono text-neutral-500 mt-1">
            6 core technical specifications ingested into the graph pipeline.
          </p>
        </div>

        <div className="border border-neutral-800 bg-[#090d14]">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#0c1017] border-b border-neutral-800 text-neutral-500">
              <tr>
                <th className="p-3">DOCUMENT</th>
                <th className="p-3">CHUNKS</th>
                <th className="p-3">FILE SIZE</th>
                <th className="p-3">INGESTION DATE</th>
                <th className="p-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60 text-neutral-300">
              {docs.map((doc) => (
                <tr key={doc.id} className="hover:bg-neutral-900/40">
                  <td className="p-3 flex items-center gap-2 text-teal-400">
                    <FileText className="w-3.5 h-3.5 text-neutral-500" />
                    <span>{doc.id}</span>
                  </td>
                  <td className="p-3">{doc.chunks}</td>
                  <td className="p-3 text-neutral-400">{doc.size}</td>
                  <td className="p-3 text-neutral-400">{doc.date}</td>
                  <td className="p-3 text-right">
                    <button className="px-2 py-1 bg-neutral-900 border border-neutral-800 hover:border-teal-500/50 text-[11px] text-neutral-300">
                      View Chunks
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (activeView === "entities") {
    const sampleEntities = [
      {
        name: "Linux Namespaces",
        type: "Kernel Primitive",
        mentions: 34,
        degree: 12,
      },
      {
        name: "Control Groups (cgroups)",
        type: "Kernel Primitive",
        mentions: 29,
        degree: 10,
      },
      { name: "runc", type: "OCI Runtime", mentions: 18, degree: 8 },
      {
        name: "containerd",
        type: "Container Runtime",
        mentions: 22,
        degree: 9,
      },
      { name: "OverlayFS", type: "Storage Driver", mentions: 15, degree: 6 },
      { name: "veth Pair", type: "Network Primitive", mentions: 12, degree: 5 },
      {
        name: "seccomp-bpf",
        type: "Security Mechanism",
        mentions: 11,
        degree: 4,
      },
      { name: "PID 1", type: "Process Isolation", mentions: 16, degree: 7 },
    ];

    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <div>
          <h2 className="text-xl font-mono text-neutral-100 font-semibold uppercase">
            Extracted Entities
          </h2>
          <p className="text-xs font-mono text-neutral-500 mt-1">
            Top extracted entities across indexed documents (
            {status?.graph_nodes ?? 430} total).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {sampleEntities.map((item) => (
            <div
              key={item.name}
              className="p-3.5 bg-[#090d14] border border-neutral-800 flex items-center justify-between"
            >
              <div className="space-y-1">
                <div className="text-xs font-mono text-teal-400 font-medium flex items-center gap-1.5">
                  <Boxes className="w-3.5 h-3.5 text-neutral-500" />
                  <span>{item.name}</span>
                </div>
                <div className="text-[10px] font-mono text-neutral-500 uppercase">
                  TYPE: {item.type}
                </div>
              </div>
              <div className="text-right font-mono text-[11px] text-neutral-400">
                <div>{item.mentions} mentions</div>
                <div className="text-neutral-500 text-[10px]">
                  {item.degree} links
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (activeView === "history") {
    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <div>
          <h2 className="text-xl font-mono text-neutral-100 font-semibold uppercase">
            Query History
          </h2>
          <p className="text-xs font-mono text-neutral-500 mt-1">
            Previous queries executed during this workstation session.
          </p>
        </div>

        <div className="border border-neutral-800 bg-[#090d14]">
          <div className="divide-y divide-neutral-800/60 font-mono text-xs">
            {history.map((h, i) => (
              <div
                key={i}
                onClick={() => onSelectHistory(h.query)}
                className="p-3.5 hover:bg-neutral-900/50 flex items-center justify-between cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <History className="w-4 h-4 text-neutral-500 group-hover:text-teal-400" />
                  <span className="text-neutral-200 group-hover:text-teal-300 font-sans text-[13px]">
                    {h.query}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-neutral-500">
                    {h.timestamp}
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-neutral-600 group-hover:text-neutral-300" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return null;
};
