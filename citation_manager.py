"""
Citation Manager - Tracks sources and ensures facts are attributable
Maintains provenance graph for debugging and trust
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from datetime import datetime
import json
import threading
import hashlib


@dataclass
class Citation:
    """Single source citation with full metadata"""
    source_id: str  # Unique identifier
    title: str
    url: str
    publisher: str
    published_date: Optional[str]
    accessed_date: str
    snippet: str
    relevance_score: float = 0.0


@dataclass
class CitedFact:
    """A fact with its supporting citations"""
    fact_text: str
    citations: List[Citation]
    agent_name: str
    turn_number: int
    confidence: str  # 'high', 'medium', 'low'


class CitationManager:
    """
    Manages citations and provenance throughout conversation.

    Features:
    - Tracks all sources used
    - Links facts to citations
    - Builds provenance graph
    - Exports bibliography and provenance data
    - Thread-safe for multi-threaded environments
    """

    def __init__(self):
        self.citations: Dict[str, Citation] = {}
        self.cited_facts: List[CitedFact] = []
        self.provenance_graph: List[Dict] = []
        self.lock = threading.Lock()  # Thread safety

    def add_citation(self, citation: Citation = None, url: str = None, title: str = None, **kwargs) -> str:
        """
        Add a citation and return its ID.

        Args:
            citation: Citation object to add (or None to create from kwargs)
            url: URL if creating citation from components
            title: Title if creating citation from components
            **kwargs: Other citation fields

        Returns:
            Source ID of the citation
        """
        if citation is None and url:
            # Auto-generate source_id from URL
            source_id = hashlib.md5(url.encode()).hexdigest()[:12]
            citation = Citation(
                source_id=source_id,
                url=url,
                title=title or "Untitled",
                publisher=kwargs.get('publisher', 'Unknown'),
                published_date=kwargs.get('published_date'),
                accessed_date=kwargs.get('accessed_date', datetime.now().strftime('%Y-%m-%d')),
                snippet=kwargs.get('snippet', ''),
                relevance_score=kwargs.get('relevance_score', 0.0)
            )

        with self.lock:
            self.citations[citation.source_id] = citation

        return citation.source_id

    def add_cited_fact(self, fact: CitedFact):
        """
        Record a fact with its supporting citations.

        Args:
            fact: CitedFact object with fact text and citations
        """
        with self.lock:
            self.cited_facts.append(fact)

            # Add to provenance graph
            for citation in fact.citations:
                self.provenance_graph.append({
                    'fact': fact.fact_text[:100] + ('...' if len(fact.fact_text) > 100 else ''),
                    'source_id': citation.source_id,
                    'url': citation.url,
                    'title': citation.title,
                    'turn': fact.turn_number,
                    'agent': fact.agent_name,
                    'confidence': fact.confidence,
                    'timestamp': datetime.now().isoformat()
                })

    def format_citation(self, citation: Citation, style: str = 'inline') -> str:
        """
        Format citation for display.

        Args:
            citation: Citation to format
            style: 'inline' or 'footnote'

        Returns:
            Formatted citation string
        """
        if style == 'inline':
            date_str = f", {citation.published_date}" if citation.published_date else ""
            return f"[{citation.publisher}{date_str}]({citation.url})"

        elif style == 'footnote':
            date_str = citation.published_date or "n.d."
            return (
                f"{citation.title}. {citation.publisher}. "
                f"{date_str}. {citation.url}"
            )

        return citation.url

    def format_bibliography(self) -> str:
        """
        Generate formatted bibliography of all sources.

        Returns:
            Markdown-formatted bibliography
        """
        with self.lock:
            if not self.citations:
                return "\n## Sources\n\nNo sources used in this conversation.\n"

            output = "\n## Sources\n\n"

            # Sort by publication date (most recent first)
            sorted_citations = sorted(
                self.citations.values(),
                key=lambda c: c.published_date or "9999",
                reverse=True
            )

            for i, citation in enumerate(sorted_citations, 1):
                date_str = citation.published_date or "Date unknown"
                output += f"{i}. **{citation.title}**  \n"
                output += f"   {citation.publisher}, {date_str}  \n"
                output += f"   {citation.url}  \n\n"

            return output

    def get_provenance_for_fact(self, fact_text: str) -> List[Citation]:
        """
        Find all citations supporting a fact.

        Args:
            fact_text: Text of the fact to look up

        Returns:
            List of citations supporting the fact
        """
        with self.lock:
            for cited_fact in self.cited_facts:
                if fact_text in cited_fact.fact_text or cited_fact.fact_text in fact_text:
                    return cited_fact.citations
        return []

    def export_provenance_graph(self, filepath: str):
        """
        Export complete provenance graph for debugging.

        Args:
            filepath: Path to save JSON file
        """
        with self.lock:
            export_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_citations': len(self.citations),
                    'total_facts': len(self.cited_facts),
                    'provenance_links': len(self.provenance_graph)
                },
                'citations': {
                    k: asdict(v) for k, v in self.citations.items()
                },
                'cited_facts': [
                    {
                        'fact': f.fact_text,
                        'agent': f.agent_name,
                        'turn': f.turn_number,
                        'confidence': f.confidence,
                        'citation_count': len(f.citations)
                    }
                    for f in self.cited_facts
                ],
                'provenance': self.provenance_graph,
                'statistics': self.get_stats()
            }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

    def get_stats(self) -> dict:
        """
        Return citation statistics.

        Returns:
            Dictionary with citation stats
        """
        with self.lock:
            avg_citations = 0
            if self.cited_facts:
                total_citations = sum(len(f.citations) for f in self.cited_facts)
                avg_citations = total_citations / len(self.cited_facts)

            # Publisher breakdown
            publishers = {}
            for citation in self.citations.values():
                publishers[citation.publisher] = publishers.get(citation.publisher, 0) + 1

            return {
                'total_sources': len(self.citations),
                'cited_facts': len(self.cited_facts),
                'provenance_links': len(self.provenance_graph),
                'average_citations_per_fact': round(avg_citations, 2),
                'publishers': publishers
            }

    def get_source_by_id(self, source_id: str) -> Optional[Citation]:
        """
        Retrieve citation by ID.

        Args:
            source_id: ID of the citation

        Returns:
            Citation object or None
        """
        with self.lock:
            return self.citations.get(source_id)

    def clear(self):
        """Clear all citation data"""
        with self.lock:
            self.citations.clear()
            self.cited_facts.clear()
            self.provenance_graph.clear()
