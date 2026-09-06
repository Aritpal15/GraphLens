import React, { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  BackgroundVariant,
} from "@xyflow/react";
import type { Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { GraphNode, GraphEdge } from "../types";

interface GraphCanvasProps {
  nodesData?: GraphNode[];
  edgesData?: GraphEdge[];
}

const FIXED_LAYOUT: Record<string, { x: number; y: number }> = {
  docker: { x: 50, y: 140 },
  overlayfs: { x: 50, y: 10 },
  runc: { x: 300, y: 140 },
  namespaces: { x: 550, y: 60 },
  cgroups: { x: 550, y: 220 },
  veth: { x: 780, y: 60 },
};

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodesData = [],
  edgesData = [],
}) => {
  const nodes: Node[] = useMemo(() => {
    return nodesData.map((n, idx) => {
      const pos = FIXED_LAYOUT[n.id] || {
        x: 80 + (idx % 3) * 250,
        y: 60 + Math.floor(idx / 3) * 150,
      };

      return {
        id: n.id,
        position: pos,
        data: {
          label: (
            <div className="text-left font-mono">
              <div className="text-[9px] uppercase tracking-wider text-teal-400/80 font-bold">
                {n.entity_type ?? "Entity"}
              </div>
              <div className="text-xs font-semibold text-neutral-100 mt-0.5 truncate">
                {n.name ?? n.id}
              </div>
            </div>
          ),
        },
        style: {
          background: "#0c1017",
          border: "1px solid rgba(20, 184, 166, 0.45)",
          borderRadius: "0px",
          padding: "10px 14px",
          width: 155,
        },
      };
    });
  }, [nodesData]);

  const edges: Edge[] = useMemo(() => {
    return edgesData.map((e, idx) => ({
      id: `e-${e.source}-${e.target}-${idx}`,
      source: e.source,
      target: e.target,
      label: e.relation_type,
      type: "smoothstep",
      labelStyle: {
        fill: "#d4d4d4",
        fontSize: 10,
        fontFamily: "monospace",
        fontWeight: 500,
      },
      labelBgStyle: {
        fill: "#080b10",
        stroke: "#262626",
        strokeWidth: 1,
      },
      labelBgPadding: [4, 2] as [number, number],
      style: { stroke: "#14b8a6", strokeWidth: 1.5 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#14b8a6",
        width: 12,
        height: 12,
      },
    }));
  }, [edgesData]);

  if (nodes.length === 0) {
    return (
      <div className="w-full h-full min-h-95 bg-[#07090e] border border-neutral-800 flex flex-col items-center justify-center font-mono text-neutral-500 text-xs">
        <span>NO ACTIVE SUBGRAPH LOADED</span>
        <span className="text-[10px] text-neutral-600 mt-1">
          Execute a query or click "Refresh Graph"
        </span>
      </div>
    );
  }

  return (
    <div className="w-full h-full min-h-100 bg-[#07090e] border border-neutral-800 relative">
      <div className="absolute top-3 left-3 z-10 font-mono text-[10px] text-neutral-400 bg-[#080b10]/90 px-2.5 py-1 border border-neutral-800 select-none flex items-center gap-2">
        <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-pulse" />
        ACTIVE SUBGRAPH ({nodes.length} NODES)
      </div>
      <div className="absolute top-3 right-3 z-10 font-mono text-[10px] text-neutral-500 select-none">
        DRAG TO PAN • SCROLL TO ZOOM
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        panOnScroll={false}
        zoomOnScroll={true}
        preventScrolling={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          color="#262626"
          gap={20}
          size={1}
          variant={BackgroundVariant.Dots}
        />
        <Controls
          showInteractive={false}
          className="bg-neutral-900 border border-neutral-800 text-neutral-300 rounded-none shadow-none [&>button]:border-neutral-800 [&>button]:rounded-none"
        />
      </ReactFlow>
    </div>
  );
};
