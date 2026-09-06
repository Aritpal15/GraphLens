import argparse
import sys
from pathlib import Path

from app.pipeline import GraphLensPipeline


def format_evidence_summary(evidence) -> str:
    lines = []
    lines.append(f"\n--- Retrievable Evidence ({len(evidence.text_chunks)} passages, {len(evidence.subgraph.nodes)} entities) ---")
    
    if evidence.text_chunks:
        lines.append("\nTop Text Chunks:")
        for tc in evidence.text_chunks:
            lines.append(f"  [{tc.chunk.chunk_id}] (Score: {tc.rerank_score:.4f}, Page {tc.chunk.page_number})")
            lines.append(f"    {tc.chunk.text[:120].strip()}...")

    if evidence.subgraph.edges:
        lines.append("\nKnowledge Graph Pathways:")
        for edge in evidence.subgraph.edges[:5]:
            lines.append(f"  ({edge.source}) -[{edge.relation_type}]-> ({edge.target})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GraphLens CLI: Hybrid RAG + Knowledge Graph Engine")
    parser.add_argument("--reindex", action="store_true", help="Force rebuild of search indices and Knowledge Graph.")
    parser.add_argument("--query", type=str, help="Submit a single question and receive an answer.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of text passages to retrieve.")
    parser.add_argument("--k-hops", type=int, default=1, help="Hop radius for knowledge graph expansion.")
    parser.add_argument("--show-evidence", action="store_true", help="Print retrieved passages and graph edges.")
    args = parser.parse_args()

    pipeline = GraphLensPipeline()

    if args.reindex:
        print("Starting corpus re-indexing...")
        pipeline.build_or_load_indices(force_rebuild=True)
        print(f"Indexing complete. Processed {len(pipeline.chunks)} chunks, {pipeline.kg.graph.number_of_nodes()} graph nodes.")
        if not args.query:
            return

    try:
        pipeline.build_or_load_indices(force_rebuild=False)
    except Exception as exc:
        print(f"Error loading pipeline indices: {exc}")
        print("Run 'python -m app.cli --reindex' after putting PDFs into data/raw_pdfs/")
        sys.exit(1)

    if args.query:
        print(f"\nQuery: {args.query}")
        answer, evidence = pipeline.query(args.query, text_top_k=args.top_k, k_hops=args.k_hops)
        print(f"\nModel: {answer.model_used}")
        print(f"\nAnswer:\n{answer.answer}")
        if answer.cited_chunk_ids:
            print(f"\nCitations: {', '.join(answer.cited_chunk_ids)}")
        if args.show_evidence:
            print(format_evidence_summary(evidence))
        return

    # Interactive Loop
    print("\n" + "=" * 60)
    print("GraphLens Interactive CLI (type 'exit' or 'quit' to stop)")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nQuestion: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break

            answer, evidence = pipeline.query(user_input, text_top_k=args.top_k, k_hops=args.k_hops)
            print(f"\n[{answer.model_used}]")
            print(f"{answer.answer}\n")
            if answer.cited_chunk_ids:
                print(f"Citations: {', '.join(answer.cited_chunk_ids)}")
            if args.show_evidence:
                print(format_evidence_summary(evidence))

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
        except Exception as e:
            print(f"Query failed: {e}")


if __name__ == "__main__":
    main()