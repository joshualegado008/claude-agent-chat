"""
Research Mode - Structured 4-phase research for comprehensive investigations
Phases: Exploration → Research → Synthesis → Report
"""

from datetime import datetime
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

from search_coordinator import SearchCoordinator, SearchContext


class ResearchPhase(Enum):
    """Research workflow phases"""
    EXPLORATION = "exploration"      # Brainstorm queries, identify gaps
    RESEARCH = "research"            # Execute searches, gather evidence
    SYNTHESIS = "synthesis"          # Analyze findings, cross-reference
    REPORT = "report"                # Generate structured report


@dataclass
class ResearchQuery:
    """Single research query with metadata"""
    query: str
    rationale: str
    priority: int  # 1-3, 1=highest
    status: str  # 'pending', 'completed', 'failed'
    search_context: Optional[SearchContext] = None


@dataclass
class ResearchSession:
    """Complete research session with all phases"""
    topic: str
    agent_name: str
    start_time: str
    end_time: Optional[str]
    current_phase: ResearchPhase
    queries: List[ResearchQuery]
    findings: List[str]  # Key findings extracted
    report: Optional[str]  # Final report
    citations_used: List[str]  # Citation IDs


class ResearchMode:
    """
    Structured research workflow for comprehensive investigations.

    Workflow:
    1. EXPLORATION: Agent plans queries based on topic
    2. RESEARCH: Execute searches, gather evidence
    3. SYNTHESIS: Analyze findings, identify patterns
    4. REPORT: Generate comprehensive report with citations

    Features:
    - Multi-query planning
    - Priority-based execution
    - Cross-reference synthesis
    - Formatted report generation
    """

    def __init__(self, search_coordinator: SearchCoordinator, config: dict):
        self.coordinator = search_coordinator
        self.config = config
        self.research_config = config.get('research', {})

        # Limits
        self.max_queries = self.research_config.get('max_queries', 8)
        self.max_queries_per_phase = self.research_config.get('max_queries_per_phase', 3)

        self.active_session: Optional[ResearchSession] = None

    def start_session(self, topic: str, agent_name: str) -> ResearchSession:
        """
        Start new research session.

        Args:
            topic: Research topic/question
            agent_name: Name of researching agent

        Returns:
            New ResearchSession
        """
        self.active_session = ResearchSession(
            topic=topic,
            agent_name=agent_name,
            start_time=datetime.now().isoformat(),
            end_time=None,
            current_phase=ResearchPhase.EXPLORATION,
            queries=[],
            findings=[],
            report=None,
            citations_used=[]
        )

        return self.active_session

    def add_query(self, query: str, rationale: str, priority: int = 2):
        """
        Add query to research plan.

        Args:
            query: Search query
            rationale: Why this query is important
            priority: 1 (high), 2 (medium), 3 (low)
        """
        if not self.active_session:
            raise ValueError("No active research session")

        if len(self.active_session.queries) >= self.max_queries:
            print(f"⚠️  Max queries ({self.max_queries}) reached, skipping: {query}")
            return

        research_query = ResearchQuery(
            query=query,
            rationale=rationale,
            priority=priority,
            status='pending'
        )

        self.active_session.queries.append(research_query)

    async def execute_research_phase(self, turn_number: int) -> List[SearchContext]:
        """
        Execute research phase: run pending queries.

        Args:
            turn_number: Current conversation turn

        Returns:
            List of SearchContext results
        """
        if not self.active_session:
            raise ValueError("No active research session")

        if self.active_session.current_phase != ResearchPhase.RESEARCH:
            raise ValueError(f"Not in RESEARCH phase (current: {self.active_session.current_phase})")

        # Sort queries by priority (1=highest)
        pending = [q for q in self.active_session.queries if q.status == 'pending']
        pending.sort(key=lambda q: q.priority)

        # Limit queries per phase
        to_execute = pending[:self.max_queries_per_phase]

        results = []
        for query in to_execute:
            print(f"🔍 Researching: {query.query} (Priority {query.priority})")

            search_ctx = await self.coordinator.execute_search(
                query=query.query,
                agent_name=self.active_session.agent_name,
                turn_number=turn_number,
                trigger_type='research_mode'
            )

            if search_ctx:
                query.status = 'completed'
                query.search_context = search_ctx
                results.append(search_ctx)

                # Track citations
                self.active_session.citations_used.extend(search_ctx.citations_added)
            else:
                query.status = 'failed'
                print(f"⚠️  Query failed: {query.query}")

        return results

    def advance_phase(self):
        """Advance to next research phase"""
        if not self.active_session:
            raise ValueError("No active research session")

        phase_order = [
            ResearchPhase.EXPLORATION,
            ResearchPhase.RESEARCH,
            ResearchPhase.SYNTHESIS,
            ResearchPhase.REPORT
        ]

        current_idx = phase_order.index(self.active_session.current_phase)
        if current_idx < len(phase_order) - 1:
            self.active_session.current_phase = phase_order[current_idx + 1]
            print(f"📊 Advanced to phase: {self.active_session.current_phase.value.upper()}")
        else:
            print("✅ Research complete (already in REPORT phase)")

    def add_finding(self, finding: str):
        """
        Record key finding during synthesis.

        Args:
            finding: Key finding text
        """
        if not self.active_session:
            raise ValueError("No active research session")

        self.active_session.findings.append(finding)

    def generate_report(self) -> str:
        """
        Generate formatted research report.

        Returns:
            Markdown-formatted report
        """
        if not self.active_session:
            raise ValueError("No active research session")

        session = self.active_session

        # Build report
        report = f"# Research Report: {session.topic}\n\n"
        report += f"**Researcher**: {session.agent_name}\n"
        report += f"**Date**: {session.start_time[:10]}\n"
        report += f"**Queries Executed**: {sum(1 for q in session.queries if q.status == 'completed')}/{len(session.queries)}\n\n"

        # Executive Summary
        report += "## Executive Summary\n\n"
        if session.findings:
            for finding in session.findings[:5]:  # Top 5 findings
                report += f"- {finding}\n"
        else:
            report += "*No key findings recorded*\n"
        report += "\n"

        # Research Queries
        report += "## Research Process\n\n"
        completed_queries = [q for q in session.queries if q.status == 'completed']

        for i, query in enumerate(completed_queries, 1):
            report += f"### Query {i}: {query.query}\n"
            report += f"**Rationale**: {query.rationale}\n\n"

            if query.search_context:
                for j, content in enumerate(query.search_context.extracted_content, 1):
                    report += f"**Source {i}.{j}**: {content.title}\n"
                    report += f"- Publisher: {content.site}\n"
                    report += f"- URL: {content.url}\n"
                    if content.published_date:
                        report += f"- Published: {content.published_date}\n"
                    report += "\n"

        # Detailed Findings
        if session.findings:
            report += "## Detailed Findings\n\n"
            for i, finding in enumerate(session.findings, 1):
                report += f"{i}. {finding}\n\n"

        # Bibliography
        if session.citations_used:
            citation_mgr = self.coordinator.citation_manager
            report += "## Sources\n\n"

            unique_citations = list(set(session.citations_used))
            for i, cid in enumerate(unique_citations, 1):
                citation = citation_mgr.get_source_by_id(cid)
                if citation:
                    date_str = citation.published_date or "n.d."
                    report += f"{i}. **{citation.title}**. {citation.publisher}, {date_str}. {citation.url}\n\n"

        # Metadata
        report += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        # Save to session
        session.report = report
        session.end_time = datetime.now().isoformat()

        return report

    def format_phase_prompt(self, phase: ResearchPhase) -> str:
        """
        Generate phase-specific prompt for agent.

        Args:
            phase: Current research phase

        Returns:
            Formatted prompt string
        """
        if not self.active_session:
            return ""

        session = self.active_session

        if phase == ResearchPhase.EXPLORATION:
            return f"""
🔬 **RESEARCH MODE: EXPLORATION PHASE**

Topic: {session.topic}

Your task: Plan comprehensive research queries.

Instructions:
1. Identify 3-5 key questions that must be answered
2. For each, explain WHY it's important
3. Prioritize: 1=critical, 2=important, 3=supplementary
4. Think about diverse perspectives and sources

Use this format:
- Query: [your search query]
- Rationale: [why this is important]
- Priority: [1, 2, or 3]

Once queries are planned, signal completion with: "EXPLORATION COMPLETE"
"""

        elif phase == ResearchPhase.RESEARCH:
            queries_count = len([q for q in session.queries if q.status == 'completed'])
            return f"""
🔍 **RESEARCH MODE: RESEARCH PHASE**

Executing {len(session.queries)} planned queries...
{queries_count} completed so far.

Search results will appear below. Review carefully and note:
- Key facts and claims
- Source credibility (date, publisher)
- Contradictions or gaps

Signal completion with: "RESEARCH COMPLETE"
"""

        elif phase == ResearchPhase.SYNTHESIS:
            return f"""
📊 **RESEARCH MODE: SYNTHESIS PHASE**

Completed {sum(1 for q in session.queries if q.status == 'completed')} searches.

Your task: Analyze and synthesize findings.

Instructions:
1. Identify key patterns and themes
2. Note contradictions or disagreements
3. Assess source quality and recency
4. Extract top 5-10 key findings
5. Note any gaps in coverage

For each key finding, use format:
FINDING: [concise statement]

Signal completion with: "SYNTHESIS COMPLETE"
"""

        elif phase == ResearchPhase.REPORT:
            return f"""
📝 **RESEARCH MODE: REPORT PHASE**

Generate comprehensive research report.

The report structure will include:
- Executive summary (top findings)
- Research process (queries + sources)
- Detailed findings
- Bibliography

Review the generated report and provide any commentary or recommendations.

Signal completion with: "REPORT COMPLETE"
"""

        return ""

    def get_session_summary(self) -> Dict:
        """Get current session statistics"""
        if not self.active_session:
            return {'active': False}

        session = self.active_session

        return {
            'active': True,
            'topic': session.topic,
            'phase': session.current_phase.value,
            'queries_total': len(session.queries),
            'queries_completed': sum(1 for q in session.queries if q.status == 'completed'),
            'queries_failed': sum(1 for q in session.queries if q.status == 'failed'),
            'queries_pending': sum(1 for q in session.queries if q.status == 'pending'),
            'findings_count': len(session.findings),
            'citations_count': len(set(session.citations_used)),
            'duration_minutes': self._calculate_duration()
        }

    def _calculate_duration(self) -> float:
        """Calculate session duration in minutes"""
        if not self.active_session:
            return 0.0

        start = datetime.fromisoformat(self.active_session.start_time)
        end = datetime.now()
        if self.active_session.end_time:
            end = datetime.fromisoformat(self.active_session.end_time)

        delta = end - start
        return round(delta.total_seconds() / 60, 1)

    def end_session(self):
        """End current research session"""
        if self.active_session:
            self.active_session.end_time = datetime.now().isoformat()
            print(f"✅ Research session ended: {self.active_session.topic}")
            self.active_session = None
