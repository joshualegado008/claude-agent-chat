"""
Search Coordinator - Main orchestration for autonomous search
Integrates budget, cache, citations, and content extraction
"""

import re
import asyncio
import aiohttp
import hashlib
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from search_budget import SearchBudget, BudgetLimits
from query_cache import QueryCache
from citation_manager import CitationManager, Citation
from content_extractor import ContentExtractor, ExtractedContent


@dataclass
class SearchResult:
    """Single search result from SearXNG"""
    title: str
    url: str
    snippet: str
    source: str
    published_date: Optional[str]
    score: float = 0.0


@dataclass
class SearchContext:
    """Complete search operation with all results and metadata"""
    query: str
    results: List[SearchResult]
    extracted_content: List[ExtractedContent]
    timestamp: str
    triggered_by: str  # 'uncertainty', 'fact_check', 'explicit_request'
    agent_name: str
    citations_added: List[str]  # Citation IDs


class SearchCoordinator:
    """
    Production-ready search orchestration.

    Features:
    - Budget enforcement (prevents cost overruns)
    - Query deduplication (caching)
    - Content extraction (clean markdown)
    - Citation tracking (provenance)
    - Intelligent trigger detection
    """

    def __init__(self, config: dict):
        self.config = config
        self.search_config = config.get('search', {})
        self.searxng_url = self.search_config.get('searxng_url', 'http://localhost:8888')

        # Initialize infrastructure components
        limits = BudgetLimits(
            max_searches_per_turn=self.search_config.get('limits', {}).get('max_per_turn', 3),
            max_searches_per_conversation=self.search_config.get('limits', {}).get('max_per_conversation', 15),
            max_requests_per_minute=self.search_config.get('limits', {}).get('max_per_minute', 10),
            cooldown_turns=self.search_config.get('limits', {}).get('cooldown_turns', 1)
        )

        self.budget = SearchBudget(limits)

        cache_config = self.search_config.get('cache', {})
        self.query_cache = QueryCache(
            ttl_minutes=cache_config.get('ttl_minutes', 15),
            cache_dir=cache_config.get('cache_dir', '.cache/search'),
            enabled=cache_config.get('enabled', True)
        )

        self.citation_manager = CitationManager()
        self.content_extractor = ContentExtractor(config)

        self.search_history: List[SearchContext] = []

        # Setup trigger patterns
        self._setup_trigger_patterns()

    def _setup_trigger_patterns(self):
        """Setup regex patterns for autonomous search triggering"""

        # Uncertainty expressions that suggest need for verification
        self.uncertainty_patterns = [
            r"I believe\s+(?:that\s+)?(.{10,100})(?:\.|,|;)",
            r"(?:it's\s+)?likely\s+that\s+(.{10,100})(?:\.|,|;)",
            r"(?:might|may|could)\s+be\s+(.{10,100})(?:\.|,|;)",
            r"I'm not (?:entirely\s+)?(?:sure|certain)\s+(?:about\s+)?(.{10,100})(?:\.|,|;)",
            r"unclear\s+(?:whether|if)\s+(.{10,100})(?:\.|,|;)",
            r"need to verify\s+(.{10,100})(?:\.|,|;)",
            r"would (?:help|benefit) to (?:check|search|research)\s+(.{10,100})(?:\.|,|;)"
        ]

        # Factual claims that should be verified
        self.fact_check_patterns = [
            r"(?:studies|research|data|statistics|evidence)\s+(?:show|suggest|indicate)(?:s)?\s+(.{10,100})(?:\.|,|;)",
            r"according to\s+(.{10,100})(?:\.|,|;)",
            r"(\d+(?:\.\d+)?%\s+of\s+.{5,50})",  # Percentages
            r"(approximately\s+\d+(?:,\d{3})*\s+.{5,50})"  # Numbers
        ]

        # Explicit search requests in thinking
        self.explicit_patterns = [
            r"let me (?:search|look up|check|find|research)\s+(.{10,100})(?:\.|,|;)",
            r"I should (?:search|look up|check|verify|research)\s+(.{10,100})(?:\.|,|;)",
            r"current (?:data|information|statistics|research)\s+(?:on|about)\s+(.{10,100})(?:\.|,|;)"
        ]

    def should_search(
        self,
        response: str,
        thinking: str,
        turn_number: int,
        agent_name: str
    ) -> Tuple[bool, str, str]:
        """
        Determine if search should be triggered.

        Args:
            response: Agent's response text
            thinking: Agent's thinking/reasoning text
            turn_number: Current turn number
            agent_name: Name of the agent

        Returns:
            Tuple of (should_search, trigger_type, query)
        """

        # Check budget first
        can_search, reason = self.budget.can_search(turn_number)
        if not can_search:
            print(f"⚠️  Search blocked for {agent_name}: {reason}")
            return False, "", ""

        # Priority 1: Explicit requests in thinking (highest priority)
        for pattern in self.explicit_patterns:
            match = re.search(pattern, thinking, re.IGNORECASE)
            if match:
                query = self._clean_query(match.group(1))
                # Check cache
                if self.query_cache.get(query):
                    print(f"✓ Using cached results for: {query}")
                    return False, "", ""
                return True, "explicit_request", query

        # Priority 2: Uncertainty markers
        for pattern in self.uncertainty_patterns:
            match = re.search(pattern, thinking + " " + response, re.IGNORECASE)
            if match:
                query = self._clean_query(match.group(1))
                if self.query_cache.get(query):
                    return False, "", ""
                return True, "uncertainty", query

        # Priority 3: Fact-check patterns
        for pattern in self.fact_check_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                query = self._clean_query(match.group(1))
                if self.query_cache.get(query):
                    return False, "", ""
                return True, "fact_check", query

        return False, "", ""

    def _clean_query(self, text: str) -> str:
        """
        Clean and optimize search query.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned query string
        """
        # Remove common stopwords (but keep if query is very short)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = text.split()

        if len(words) > 3:
            words = [w for w in words if w.lower() not in stopwords]

        # Limit length to 10 words
        query = ' '.join(words[:10])

        return query.strip()

    async def execute_search(
        self,
        query: str,
        agent_name: str,
        turn_number: int,
        trigger_type: str
    ) -> Optional[SearchContext]:
        """
        Execute complete search pipeline.

        Pipeline:
        1. Check cache
        2. Query SearXNG
        3. Extract content from top results
        4. Create citations
        5. Cache results

        Args:
            query: Search query
            agent_name: Name of agent triggering search
            turn_number: Current turn number
            trigger_type: Type of trigger

        Returns:
            SearchContext or None if search fails
        """

        # Check cache first
        cached = self.query_cache.get(query)
        if cached:
            print(f"✓ Using cached search results")
            return cached

        try:
            # Query SearXNG
            results = await self._query_searxng(query)
            if not results:
                print(f"⚠️  No search results found")
                self.budget.record_search(turn_number, success=False)
                return None

            # Extract content from top 3 results (parallel)
            extraction_tasks = [
                self.content_extractor.extract(result.url)
                for result in results[:3]
            ]
            extracted_contents = await asyncio.gather(*extraction_tasks)
            extracted_contents = [e for e in extracted_contents if e is not None]

            if not extracted_contents:
                print(f"⚠️  Content extraction failed for all results")
                self.budget.record_search(turn_number, success=False)
                return None

            # Create citations
            citation_ids = []
            for content in extracted_contents:
                citation = Citation(
                    source_id=self._generate_source_id(content.url),
                    title=content.title,
                    url=content.url,
                    publisher=content.site,
                    published_date=content.published_date,
                    accessed_date=datetime.now().strftime('%Y-%m-%d'),
                    snippet=content.excerpt,
                    relevance_score=0.0
                )
                cid = self.citation_manager.add_citation(citation)
                citation_ids.append(cid)

            # Create search context
            search_ctx = SearchContext(
                query=query,
                results=results,
                extracted_content=extracted_contents,
                timestamp=datetime.now().isoformat(),
                triggered_by=trigger_type,
                agent_name=agent_name,
                citations_added=citation_ids
            )

            # Cache and record
            self.query_cache.set(query, search_ctx)
            self.search_history.append(search_ctx)
            self.budget.record_search(turn_number, success=True)

            return search_ctx

        except Exception as e:
            print(f"❌ Search failed: {e}")
            self.budget.record_search(turn_number, success=False)
            return None

    async def _query_searxng(self, query: str) -> List[SearchResult]:
        """
        Query SearXNG and parse results.

        Args:
            query: Search query

        Returns:
            List of SearchResult objects
        """
        engines = self.search_config.get('engines', ['google', 'duckduckgo'])

        params = {
            'q': query,
            'format': 'json',
            'engines': ','.join(engines),
            'language': 'en'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.searxng_url}/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        print(f"⚠️  SearXNG returned status {response.status}")
                        return []

                    data = await response.json()
                    results = []

                    for item in data.get('results', [])[:8]:
                        results.append(SearchResult(
                            title=item.get('title', ''),
                            url=item.get('url', ''),
                            snippet=item.get('content', ''),
                            source=item.get('engine', 'unknown'),
                            published_date=item.get('publishedDate'),
                            score=item.get('score', 0.0)
                        ))

                    return results

        except asyncio.TimeoutError:
            print(f"⚠️  SearXNG query timeout")
            return []
        except Exception as e:
            print(f"⚠️  SearXNG query failed: {e}")
            return []

    def _generate_source_id(self, url: str) -> str:
        """Generate unique source ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def format_search_for_context(self, search_ctx: SearchContext) -> str:
        """
        Format search results for injection into agent context.

        Args:
            search_ctx: SearchContext with results

        Returns:
            Formatted string for agent context
        """
        output = f"\n{'='*60}\n"
        output += f"🔍 Search Results: \"{search_ctx.query}\"\n"
        output += f"{'='*60}\n\n"

        for i, content in enumerate(search_ctx.extracted_content, 1):
            date_str = ""
            if content.published_date:
                date_str = f" (Published: {content.published_date})"

            output += f"**Source {i}: {content.title}**{date_str}\n"
            output += f"Publisher: {content.site}\n"
            output += f"URL: {content.url}\n\n"
            output += f"{content.excerpt}\n\n"

            if i < len(search_ctx.extracted_content):
                output += "---\n\n"

        output += "\n**Instructions:**\n"
        output += "- Use these sources to inform your response\n"
        output += "- Cite sources when making claims based on this information\n"
        output += "- Note publish dates when assessing currency\n"
        output += f"\n{'='*60}\n"

        return output

    def get_summary_stats(self) -> dict:
        """Get comprehensive search statistics"""
        trigger_breakdown = {}
        for search in self.search_history:
            trigger = search.triggered_by
            trigger_breakdown[trigger] = trigger_breakdown.get(trigger, 0) + 1

        return {
            'total_searches': len(self.search_history),
            'budget': self.budget.get_stats(),
            'citations': self.citation_manager.get_stats(),
            'cache': self.query_cache.get_stats(),
            'trigger_breakdown': trigger_breakdown
        }
