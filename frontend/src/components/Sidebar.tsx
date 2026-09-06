import React, { useRef } from "react";
import {
  Terminal,
  Share2,
  FileText,
  Boxes,
  History,
  UploadCloud,
  RotateCw,
  Plus,
  User,
} from "lucide-react";
import type { SystemStatus } from "../types";

interface SidebarProps {
  status: SystemStatus | null;
  activeView: string;
  setActiveView: (view: string) => void;
  queryCount: number;
  onRefreshGraph: () => void;
  onNewSession: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  status,
  activeView,
  setActiveView,
  queryCount,
  onRefreshGraph,
  onNewSession,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const navItems = [
    { id: "research", label: "Research Session", icon: Terminal },
    { id: "graph", label: "Knowledge Graph", icon: Share2 },
    { id: "documents", label: "Documents", icon: FileText, count: 6 },
    {
      id: "entities",
      label: "Entities",
      icon: Boxes,
      count: status?.graph_nodes ?? 430,
    },
    { id: "history", label: "Query History", icon: History, count: queryCount },
  ];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      alert(
        `Selected ${files.length} document(s) for ingestion: ${files[0].name}`,
      );
    }
  };

  return (
    <aside className="w-62.5 min-w-62.5 h-screen bg-[#080b10] border-r border-neutral-800 flex flex-col justify-between select-none">
      {/* Hidden File Input for Document Upload */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
        multiple
        accept=".pdf,.txt,.md"
      />

      {/* Brand Header */}
      <div className="p-4 border-b border-neutral-800/80">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-teal-500/10 border border-teal-500/40 flex items-center justify-center text-teal-400 font-mono font-bold text-sm">
            N
          </div>
          <div>
            <div className="font-mono text-sm font-semibold tracking-wider text-neutral-100 uppercase">
              GraphLens
            </div>
            <div className="text-[10px] font-mono text-neutral-500 tracking-tight">
              GRAPH RAG WORKSTATION
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Section */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 px-3 mb-2">
            Workspace
          </div>
          <nav className="space-y-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs font-sans rounded-none transition-colors cursor-pointer ${
                    isActive
                      ? "bg-neutral-900 text-teal-400 border-l-2 border-teal-400 font-medium"
                      : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/50"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.count !== undefined && (
                    <span className="font-mono text-[10px] text-neutral-500">
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Live Session Stats */}
        <div className="pt-2 border-t border-neutral-800/60">
          <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 px-3 mb-2">
            Current Session
          </div>
          <div className="px-3 space-y-2 text-xs font-mono">
            <div className="flex justify-between items-center text-neutral-400">
              <span className="text-neutral-500 text-[11px]">
                Documents Indexed
              </span>
              <span className="text-neutral-200">{status ? 6 : "—"}</span>
            </div>
            <div className="flex justify-between items-center text-neutral-400">
              <span className="text-neutral-500 text-[11px]">
                Entities Extracted
              </span>
              <span className="text-neutral-200">
                {status?.graph_nodes ?? "—"}
              </span>
            </div>
            <div className="flex justify-between items-center text-neutral-400">
              <span className="text-neutral-500 text-[11px]">
                Relationships Found
              </span>
              <span className="text-neutral-200">
                {status?.graph_edges ?? "—"}
              </span>
            </div>
            <div className="flex justify-between items-center text-neutral-400">
              <span className="text-neutral-500 text-[11px]">
                Queries Answered
              </span>
              <span className="text-neutral-200">{queryCount}</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="pt-2 border-t border-neutral-800/60">
          <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 px-3 mb-2">
            Quick Actions
          </div>
          <div className="space-y-1 px-1">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-teal-400/90 bg-teal-500/10 border border-teal-500/30 hover:bg-teal-500/20 transition-colors cursor-pointer"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload Documents</span>
            </button>
            <button
              onClick={onRefreshGraph}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/60 transition-colors border border-transparent cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Refresh Graph</span>
            </button>
            <button
              onClick={onNewSession}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/60 transition-colors border border-transparent cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Session</span>
            </button>
          </div>
        </div>
      </div>

      {/* User / Session Footer */}
      <div className="p-3 border-t border-neutral-800 bg-[#06080c] flex items-center gap-2.5">
        <div className="w-6 h-6 rounded-none bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-300">
          <User className="w-3.5 h-3.5" />
        </div>
        <div className="truncate">
          <div className="text-xs text-neutral-200 font-medium truncate">
            AP - Researcher
          </div>
          <div className="text-[10px] font-mono text-teal-500 flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-teal-400 inline-block" />
            session_0842 : active
          </div>
        </div>
      </div>
    </aside>
  );
};
