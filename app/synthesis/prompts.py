from typing import List
from app.evidence.schemas import UnifiedEvidencePacket


def format_text_chunks_for_prompt(packet: UnifiedEvidencePacket) -> str:
    if not packet.text_chunks:
        return "None available."

    lines: List[str] = []
    for item in packet.text_chunks:
        chunk = item.chunk
        lines.append(
            f"[{chunk.chunk_id}] (Document: {chunk.filename}, Page: {chunk.page_number}, Rank: {item.rank})\n"
            f"{chunk.text.strip()}\n"
        )
    return "\n".join(lines)


def format_subgraph_for_prompt(packet: UnifiedEvidencePacket) -> str:
    subgraph = packet.subgraph
    if not subgraph.nodes and not subgraph.edges:
        return "None available."

    lines: List[str] = []

    if subgraph.nodes:
        lines.append("Entities:")
        for node in subgraph.nodes:
            alias_str = f" (Aliases: {', '.join(node.aliases)})" if node.aliases else ""
            desc = f" - {node.description}" if node.description else ""
            lines.append(f"  - {node.canonical_name} [{node.entity_type}]{alias_str}{desc}")

    if subgraph.edges:
        lines.append("\nRelationships:")
        for edge in subgraph.edges:
            desc = f": {edge.description}" if edge.description else ""
            lines.append(f"  - ({edge.source}) --[{edge.relation_type}]--> ({edge.target}){desc}")

    if subgraph.paths:
        lines.append("\nDiscovered Relational Pathways:")
        for path in subgraph.paths:
            lines.append(f"  - {' -> '.join(path)}")

    return "\n".join(lines)


def build_synthesis_prompt(packet: UnifiedEvidencePacket) -> str:
    text_context = format_text_chunks_for_prompt(packet)
    graph_context = format_subgraph_for_prompt(packet)

    prompt = f"""You are GraphLens, an authoritative technical assistant specializing in complex systems architecture and operational documentation.

Answer the user query thoroughly using ONLY the provided text chunks and knowledge graph relations.

### Instructions:
1. Ground every claim directly in the evidence.
2. When referencing specific documentation text, cite the exact source chunk using brackets (e.g., [doc_test_p1_c0]).
3. Explicitly highlight multi-hop structural relationships or architectural pathways discovered via the knowledge graph.
4. If the provided evidence is insufficient to answer completely, state clearly what information is missing rather than speculating.

### User Query:
{packet.query}

### Retrieved Text Passages:
{text_context}

### Knowledge Graph Context:
{graph_context}

### Synthesized Response:"""
    return prompt