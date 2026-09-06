export interface SystemStatus {
  indexed_chunks: number;
  graph_nodes: number;
  graph_edges: number;
  indices_ready: boolean;
  status: string;
}

export interface GraphNode {
  id: string;
  name?: string;
  label?: string;
  entity_type?: string;
  community?: number;
  degree?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation_type: string;
  weight?: number;
}

export interface ChunkCitation {
  chunk_id: string;
  source_doc: string;
  page_num?: number;
  text: string;
  score?: number;
}

export interface ReasoningStep {
  from: string;
  relation: string;
  to: string;
}

export interface EvidenceChunk {
  chunk_id: string;
  text: string;
  doc_id: string;
  score: number;
}

export interface QueryResponse {
  query: string;
  answer: string;
  confidence?: number;
  latency?: number;
  traversal_depth?: number;
  scope_documents?: number;
  cited_chunk_ids: string[];
  evidence?: ChunkCitation[];
  subgraph?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  reasoning_path?: ReasoningStep[];
}

export interface GraphInsights {
  top_entities: Array<{
    name: string;
    count: number;
    pct: string;
  }>;
  communities_count: number;
  documents_count: number;
  total_nodes: number;
  total_edges: number;
}
