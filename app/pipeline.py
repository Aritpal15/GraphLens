import logging
from pathlib import Path
from typing import List, Optional, Tuple

from app.config.settings import settings
from app.evidence.assembler import EvidenceAssembler
from app.evidence.schemas import UnifiedEvidencePacket
from app.graph.batch_pipeline import BatchGraphExtractor
from app.graph.knowledge_graph import KnowledgeGraph
from app.graph.traversal import GraphTraverser
from app.ingestion.chunker import PageAwareChunker
from app.ingestion.extractor import PDFExtractor
from app.ingestion.schemas import TextChunk
from app.retrieval.pipeline import RetrievalPipeline
from app.synthesis.synthesizer import AnswerSynthesizer, SynthesizedAnswer

logger = logging.getLogger(__name__)


class GraphLensPipeline:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (settings.BASE_DIR / "data")
        self.raw_pdf_dir = self.data_dir / "raw_pdfs"
        self.indices_dir = self.data_dir / "indices"
        self.kg_path = self.data_dir / "knowledge_graph.json"

        # Ingestion components
        self.chunker = PageAwareChunker()

        # In-memory chunk cache
        self.chunks: List[TextChunk] = []

        # Graph components
        self.kg = KnowledgeGraph()
        self.batch_graph_extractor = BatchGraphExtractor()
        self.traverser: Optional[GraphTraverser] = None

        # Retrieval components
        self.retrieval_pipeline = RetrievalPipeline(
            rrf_k=60,
            embedding_model=settings.EMBEDDING_MODEL_NAME,
            reranker_model=settings.RERANKER_MODEL_NAME,
        )

        # Evidence & Synthesis components
        self.evidence_assembler: Optional[EvidenceAssembler] = None
        self.synthesizer = AnswerSynthesizer()

    def build_or_load_indices(self, force_rebuild: bool = False) -> None:
        self.indices_dir.mkdir(parents=True, exist_ok=True)

        can_load_kg = not force_rebuild and self.kg_path.exists()

        if can_load_kg:
            logger.info(f"Loading existing Knowledge Graph from {self.kg_path}...")
            self.kg = KnowledgeGraph.load_json(self.kg_path)
            self._load_and_index_text_chunks()
        else:
            logger.info("Building indices and Knowledge Graph from raw PDF documents...")
            self._ingest_and_index_corpus()

        self.traverser = GraphTraverser(self.kg)
        self.evidence_assembler = EvidenceAssembler(
            retrieval_pipeline=self.retrieval_pipeline,
            graph_traverser=self.traverser,
        )

    def _extract_all_chunks(self) -> List[TextChunk]:
        pdf_files = list(self.raw_pdf_dir.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF documents found in {self.raw_pdf_dir}")
            return []

        all_chunks: List[TextChunk] = []
        for pdf_path in pdf_files:
            _, pages = PDFExtractor.extract_document(pdf_path)
            chunks = self.chunker.chunk_document(pages)
            all_chunks.extend(chunks)

        self.chunks = all_chunks
        return all_chunks

    def _load_and_index_text_chunks(self) -> None:
        chunks = self._extract_all_chunks()
        if chunks:
            logger.info(f"Populating text search indices with {len(chunks)} chunks...")
            self.retrieval_pipeline.index_chunks(chunks)

    def _ingest_and_index_corpus(self) -> None:
        chunks = self._extract_all_chunks()
        if not chunks:
            return

        logger.info(f"Indexing {len(chunks)} chunks into BM25 and FAISS...")
        self.retrieval_pipeline.index_chunks(chunks)

        logger.info("Extracting entities and relationships for the Knowledge Graph...")
        entities, relationships, _ = self.batch_graph_extractor.process_chunks(chunks)
        self.kg.populate(entities, relationships)
        self.kg.save_json(self.kg_path)
        logger.info(f"Knowledge Graph saved with {self.kg.graph.number_of_nodes()} nodes and {self.kg.graph.number_of_edges()} edges.")

    def query(
        self,
        question: str,
        text_top_k: int = 5,
        k_hops: int = 1,
    ) -> Tuple[SynthesizedAnswer, UnifiedEvidencePacket]:
        if not self.evidence_assembler:
            raise RuntimeError("Pipeline is not initialized. Run build_or_load_indices() first.")

        evidence_packet = self.evidence_assembler.assemble(
            query=question,
            text_top_k=text_top_k,
            k_hops=k_hops,
        )

        answer = self.synthesizer.synthesize(evidence_packet)
        return answer, evidence_packet