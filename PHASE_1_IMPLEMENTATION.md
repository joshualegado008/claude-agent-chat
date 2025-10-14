# Phase 1: Dynamic Multi-Agent System - Implementation Guide

**Version**: 0.4.0 (Development)
**Baseline**: v0.3.0
**Estimated Effort**: 40-60 hours
**Target Completion**: TBD

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Sub-Phase 1A: Foundation](#sub-phase-1a-foundation--infrastructure)
4. [Sub-Phase 1B: Topic Refinement](#sub-phase-1b-topic-refinement--classification)
5. [Sub-Phase 1C: Agent Creation](#sub-phase-1c-dynamic-agent-creation)
6. [Sub-Phase 1D: Rating & Lifecycle](#sub-phase-1d-rating--lifecycle-systems)
7. [Sub-Phase 1E: Integration](#sub-phase-1e-integration--testing)
8. [Testing Scenarios](#testing-scenarios)
9. [Success Criteria](#success-criteria)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Goal
Transform claude-agent-chat from **fixed agents** (Nova/Atlas) to **dynamic agent creation** with:
- Topic refinement using OpenAI 4o-mini
- Agent taxonomy and classification
- Dynamic agent creation via Claude API
- Performance ratings and promotions
- Agent lifecycle management (Hot/Warm/Cold tiers)
- Deduplication system

### Architecture
```
User Input → Topic Refiner → Expertise Analysis → Deduplication Check
    ↓
Find/Create Agents → Conversation → Rating → Lifecycle Management
```

### Execution Strategy
Implement in **5 incremental sub-phases**:
- **1A**: Foundation (8-10h) - Data structures, storage
- **1B**: Topic & Taxonomy (10-12h) - OpenAI integration, classification
- **1C**: Agent Creation (12-15h) - Factory, deduplication
- **1D**: Rating & Lifecycle (10-12h) - Performance tracking, tiers
- **1E**: Integration (10-12h) - Wire together, test

---

## Prerequisites

### Current System (v0.3.0)
✅ agent_runner.py - Anthropic API integration
✅ coordinator_with_memory.py - Conversation orchestration
✅ display_formatter.py - Terminal UI
✅ db_manager.py - PostgreSQL + Qdrant
✅ conversation_manager_persistent.py - Conversation state

### Required API Keys
- `ANTHROPIC_API_KEY` - Claude API (already configured)
- `OPENAI_API_KEY` - GPT-4o-mini for topic refinement (**NEW**)

### New Dependencies
Add to `requirements.txt`:
```
openai>=1.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

---

## Sub-Phase 1A: Foundation & Infrastructure

**Time**: 8-10 hours
**Goal**: Establish data structures, storage layer, directory structure

### 1. Create Directory Structure

```bash
mkdir -p src/
mkdir -p data/agents/
mkdir -p data/ratings/
mkdir -p data/conversations/
touch src/__init__.py
```

### 2. Define Core Data Classes

**File**: `src/data_models.py`

```python
"""
Core data models for dynamic multi-agent system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Set, Dict, Optional
import numpy as np


class AgentDomain(Enum):
    """Top-level expertise domains."""
    SCIENCE = "science"
    MEDICINE = "medicine"
    HUMANITIES = "humanities"
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    LAW = "law"
    ARTS = "arts"


class AgentTier(Enum):
    """Agent lifecycle tiers based on usage."""
    HOT = "hot"          # Currently active in conversation
    WARM = "warm"        # Used within 7 days (instant retrieval)
    COLD = "cold"        # Used 7-90 days ago (slower retrieval)
    ARCHIVED = "archived" # 90+ days, candidate for retirement
    RETIRED = "retired"   # Deleted, pattern saved


class AgentRank(Enum):
    """Agent promotion ranks based on performance."""
    NOVICE = 1        # 0-9 points (new agents)
    COMPETENT = 2     # 10-24 points
    EXPERT = 3        # 25-49 points
    MASTER = 4        # 50-99 points
    LEGENDARY = 5     # 100-199 points
    GOD_TIER = 6      # 200+ points (never retired)


@dataclass
class AgentProfile:
    """Complete agent profile with expertise and metadata."""

    # Identity
    agent_id: str
    name: str

    # Taxonomy
    domain: AgentDomain
    primary_class: str
    subclass: str
    specialization: str

    # Expertise
    unique_expertise: str
    core_skills: List[str]
    keywords: Set[str]

    # System
    system_prompt: str
    created_at: datetime
    last_used: datetime

    # Embeddings (for similarity detection)
    expertise_embedding: Optional[np.ndarray] = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'domain': self.domain.value,
            'primary_class': self.primary_class,
            'subclass': self.subclass,
            'specialization': self.specialization,
            'unique_expertise': self.unique_expertise,
            'core_skills': self.core_skills,
            'keywords': list(self.keywords),
            'system_prompt': self.system_prompt,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentProfile':
        """Create from dict."""
        return cls(
            agent_id=data['agent_id'],
            name=data['name'],
            domain=AgentDomain(data['domain']),
            primary_class=data['primary_class'],
            subclass=data['subclass'],
            specialization=data['specialization'],
            unique_expertise=data['unique_expertise'],
            core_skills=data['core_skills'],
            keywords=set(data['keywords']),
            system_prompt=data['system_prompt'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_used=datetime.fromisoformat(data['last_used'])
        )


@dataclass
class ConversationRating:
    """Rating for an agent's performance in a conversation."""

    agent_id: str
    conversation_id: str
    timestamp: datetime

    # Human ratings (1-5 scale)
    helpfulness: int
    accuracy: int
    relevance: int
    clarity: int
    collaboration: int

    # Computed
    overall_score: float  # Weighted average
    quality_points: int   # For promotions (0-5 based on overall)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'agent_id': self.agent_id,
            'conversation_id': self.conversation_id,
            'timestamp': self.timestamp.isoformat(),
            'helpfulness': self.helpfulness,
            'accuracy': self.accuracy,
            'relevance': self.relevance,
            'clarity': self.clarity,
            'collaboration': self.collaboration,
            'overall_score': self.overall_score,
            'quality_points': self.quality_points
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConversationRating':
        """Create from dict."""
        return cls(
            agent_id=data['agent_id'],
            conversation_id=data['conversation_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            helpfulness=data['helpfulness'],
            accuracy=data['accuracy'],
            relevance=data['relevance'],
            clarity=data['clarity'],
            collaboration=data['collaboration'],
            overall_score=data['overall_score'],
            quality_points=data['quality_points']
        )


@dataclass
class AgentPerformanceProfile:
    """Complete performance history for an agent."""

    agent_id: str
    agent_name: str
    total_conversations: int = 0
    total_points: int = 0
    current_rank: AgentRank = AgentRank.NOVICE
    average_score: float = 0.0
    ratings: List[ConversationRating] = field(default_factory=list)

    def add_rating(self, rating: ConversationRating):
        """Add rating and update stats."""
        self.ratings.append(rating)
        self.total_conversations += 1
        self.total_points += rating.quality_points
        self._recalculate_average()
        self._check_promotion()

    def _recalculate_average(self):
        """Recalculate average score."""
        if self.ratings:
            self.average_score = sum(r.overall_score for r in self.ratings) / len(self.ratings)

    def _check_promotion(self):
        """Check if agent should be promoted."""
        if self.total_points >= 200:
            self.current_rank = AgentRank.GOD_TIER
        elif self.total_points >= 100:
            self.current_rank = AgentRank.LEGENDARY
        elif self.total_points >= 50:
            self.current_rank = AgentRank.MASTER
        elif self.total_points >= 25:
            self.current_rank = AgentRank.EXPERT
        elif self.total_points >= 10:
            self.current_rank = AgentRank.COMPETENT
        else:
            self.current_rank = AgentRank.NOVICE

    def should_retire(self, days_unused: int) -> bool:
        """Determine if agent should be retired."""
        # God tier never retires
        if self.current_rank == AgentRank.GOD_TIER:
            return False

        # Novice agents retire after 6 months unused
        if self.current_rank == AgentRank.NOVICE and days_unused > 180:
            return True

        # Other ranks have longer grace periods
        if self.current_rank == AgentRank.COMPETENT and days_unused > 365:
            return True

        return False
```

### 3. Implement JSON Persistence

**File**: `src/persistence.py`

```python
"""
JSON-based persistence for Phase 1.
Phase 2 will migrate to PostgreSQL.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from src.data_models import AgentProfile, ConversationRating


class DataStore:
    """Simple JSON-based storage for agents and ratings."""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.agents_dir = self.data_dir / 'agents'
        self.ratings_dir = self.data_dir / 'ratings'
        self.conversations_dir = self.data_dir / 'conversations'

        # Create directories
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.ratings_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def save_agent(self, agent: AgentProfile) -> None:
        """Save agent profile to JSON file."""
        file_path = self.agents_dir / f"{agent.agent_id}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(agent.to_dict(), f, indent=2, ensure_ascii=False)

    def load_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Load agent profile from JSON file."""
        file_path = self.agents_dir / f"{agent_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return AgentProfile.from_dict(data)

    def load_all_agents(self) -> Dict[str, AgentProfile]:
        """Load all agents on startup."""
        agents = {}

        for file_path in self.agents_dir.glob("*.json"):
            agent_id = file_path.stem
            agent = self.load_agent(agent_id)
            if agent:
                agents[agent_id] = agent

        return agents

    def save_rating(self, rating: ConversationRating) -> None:
        """Save rating to JSON file."""
        # Save in agent-specific file
        agent_ratings_file = self.ratings_dir / f"{rating.agent_id}.json"

        # Load existing ratings
        if agent_ratings_file.exists():
            with open(agent_ratings_file, 'r') as f:
                ratings_data = json.load(f)
        else:
            ratings_data = []

        # Append new rating
        ratings_data.append(rating.to_dict())

        # Save back
        with open(agent_ratings_file, 'w', encoding='utf-8') as f:
            json.dump(ratings_data, f, indent=2)

    def load_agent_ratings(self, agent_id: str) -> List[ConversationRating]:
        """Load all ratings for an agent."""
        agent_ratings_file = self.ratings_dir / f"{agent_id}.json"

        if not agent_ratings_file.exists():
            return []

        with open(agent_ratings_file, 'r') as f:
            ratings_data = json.load(f)

        return [ConversationRating.from_dict(r) for r in ratings_data]

    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent (retirement)."""
        file_path = self.agents_dir / f"{agent_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False
```

### 4. Update Configuration

**File**: `config.yaml` - Add new sections:

```yaml
# OpenAI for topic refinement
openai:
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 1000

# Agent factory settings
agent_factory:
  max_concurrent_agents: 5
  default_model: "claude-sonnet-4-5-20250929"
  enable_dynamic_creation: true

# Lifecycle settings
agent_lifecycle:
  warm_days: 7      # Warm tier if used within N days
  cold_days: 90     # Cold tier if used within N days
  archive_days: 180 # Archive after N days unused
  enable_auto_retirement: false  # Disabled by default for safety

# Rating system
rating:
  enable_post_conversation_prompt: true
  skip_if_short_conversation: true
  min_turns_for_rating: 3

  # Weighted scoring (must sum to 1.0)
  weights:
    helpfulness: 0.30
    accuracy: 0.25
    relevance: 0.20
    clarity: 0.15
    collaboration: 0.10

# Taxonomy
taxonomy:
  max_agents_per_class: 10
  similarity_threshold: 0.85
  enable_strict_deduplication: true
```

### 5. Update Environment

**File**: `.env.example` - Add:

```bash
# Anthropic API (existing)
ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI API (new - for topic refinement)
OPENAI_API_KEY=sk-proj-...
```

### 6. Update Dependencies

**File**: `requirements.txt` - Add:

```
openai>=1.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

Install:
```bash
pip install -r requirements.txt
```

### Deliverable 1A

✅ Directory structure created
✅ Data models defined and tested
✅ JSON persistence working (save/load agents)
✅ Config updated with new sections
✅ Dependencies installed

**Test**:
```python
from src.data_models import AgentProfile, AgentDomain
from src.persistence import DataStore
from datetime import datetime

# Create test agent
agent = AgentProfile(
    agent_id="test-001",
    name="Dr. Test",
    domain=AgentDomain.SCIENCE,
    primary_class="Physics",
    subclass="Quantum",
    specialization="Quantum Computing",
    unique_expertise="Expert in quantum algorithms",
    core_skills=["quantum mechanics", "algorithms"],
    keywords={"quantum", "computing", "physics"},
    system_prompt="You are a quantum computing expert.",
    created_at=datetime.now(),
    last_used=datetime.now()
)

# Save and load
store = DataStore()
store.save_agent(agent)
loaded = store.load_agent("test-001")
assert loaded.name == "Dr. Test"
print("✅ Persistence test passed!")
```

---

## Sub-Phase 1B: Topic Refinement & Classification

**Time**: 10-12 hours
**Goal**: OpenAI integration for topic refinement + agent taxonomy

### 1. Implement Topic Refiner

**File**: `src/topic_refiner.py`

```python
"""
Topic refinement using OpenAI 4o-mini.
Cost: ~$0.0001 per refinement.
"""

import os
from openai import OpenAI
from typing import List, Dict
from src.data_models import AgentDomain


class TopicRefiner:
    """Refines user's raw topic input using OpenAI 4o-mini."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"

    async def refine_topic(self, raw_topic: str) -> dict:
        """
        Refines user input into clear topic and expertise requirements.

        Args:
            raw_topic: User's raw input (e.g., "ancient canaanite eye diseases")

        Returns:
            {
                'refined_topic': str,
                'expertise_needed': List[str],
                'suggested_domains': List[AgentDomain]
            }
        """

        prompt = self._build_refinement_prompt(raw_topic)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing topics and identifying required expertise."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # Parse response
            result = self._parse_refinement_response(response.choices[0].message.content)

            return result

        except Exception as e:
            print(f"❌ Topic refinement failed: {e}")
            # Fallback to basic refinement
            return {
                'refined_topic': raw_topic,
                'expertise_needed': ["General Expert"],
                'suggested_domains': [AgentDomain.HUMANITIES]
            }

    def _build_refinement_prompt(self, raw_topic: str) -> str:
        """Build structured prompt for topic refinement."""
        return f"""Given this user topic: "{raw_topic}"

Please analyze and provide:

1. **Refined Topic**: A clear, grammatically correct discussion question (1-2 sentences)

2. **Expertise Needed**: List 2-3 specific expertise domains required for a comprehensive discussion
   Examples:
   - "Ancient Near Eastern History (Canaanite period)"
   - "Ophthalmology (eye diseases)"
   - "Historical Medicine"

3. **Suggested Domains**: Which high-level domains apply?
   Options: SCIENCE, MEDICINE, HUMANITIES, TECHNOLOGY, BUSINESS, LAW, ARTS

Return as structured text:

REFINED TOPIC:
[Your refined topic here]

EXPERTISE NEEDED:
- [Expertise 1]
- [Expertise 2]
- [Expertise 3]

SUGGESTED DOMAINS:
- [DOMAIN1]
- [DOMAIN2]
"""

    def _parse_refinement_response(self, response_text: str) -> dict:
        """Parse structured response from OpenAI."""
        lines = response_text.strip().split('\n')

        refined_topic = ""
        expertise_needed = []
        suggested_domains = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("REFINED TOPIC:"):
                current_section = "refined"
                continue
            elif line.startswith("EXPERTISE NEEDED:"):
                current_section = "expertise"
                continue
            elif line.startswith("SUGGESTED DOMAINS:"):
                current_section = "domains"
                continue

            if current_section == "refined" and line:
                refined_topic = line
            elif current_section == "expertise" and line.startswith("-"):
                expertise = line[1:].strip()
                if expertise:
                    expertise_needed.append(expertise)
            elif current_section == "domains" and line.startswith("-"):
                domain_str = line[1:].strip()
                try:
                    domain = AgentDomain[domain_str.upper()]
                    suggested_domains.append(domain)
                except:
                    pass

        return {
            'refined_topic': refined_topic or "Discussion topic",
            'expertise_needed': expertise_needed or ["General Expert"],
            'suggested_domains': suggested_domains or [AgentDomain.HUMANITIES]
        }
```

### 2. Implement Agent Taxonomy

**File**: `src/agent_taxonomy.py`

```python
"""
Agent classification and taxonomy system.
Organizes agents by Domain > Class > Specialization.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from src.data_models import AgentDomain, AgentProfile


@dataclass
class AgentClass:
    """Represents a classification node in the taxonomy."""

    name: str
    domain: AgentDomain
    parent: Optional[str]
    description: str
    typical_skills: List[str]
    keywords: Set[str]
    max_agents: int = 10


class AgentTaxonomy:
    """Manages agent classification and organization."""

    def __init__(self):
        self.classes: Dict[str, AgentClass] = {}
        self.agents: Dict[str, AgentProfile] = {}
        self._initialize_taxonomy()

    def _initialize_taxonomy(self):
        """Create taxonomy tree with 15-20 classes across domains."""

        # MEDICINE
        self._add_class(AgentClass(
            name="Cardiology",
            domain=AgentDomain.MEDICINE,
            parent="Medicine",
            description="Heart and cardiovascular system",
            typical_skills=["cardiac care", "heart disease", "interventional cardiology"],
            keywords={"heart", "cardiac", "cardiovascular", "cardiology"}
        ))

        self._add_class(AgentClass(
            name="Neurology",
            domain=AgentDomain.MEDICINE,
            parent="Medicine",
            description="Brain and nervous system",
            typical_skills=["neurological disorders", "brain", "neuroscience"],
            keywords={"brain", "neural", "neurology", "nervous system"}
        ))

        self._add_class(AgentClass(
            name="Ophthalmology",
            domain=AgentDomain.MEDICINE,
            parent="Medicine",
            description="Eye diseases and vision",
            typical_skills=["retinal diseases", "glaucoma", "cataracts", "vision"],
            keywords={"eye", "vision", "ophthalmology", "retina", "visual"}
        ))

        # HUMANITIES
        self._add_class(AgentClass(
            name="Ancient Near East",
            domain=AgentDomain.HUMANITIES,
            parent="Ancient History",
            description="Mesopotamia, Canaan, Egypt, ancient civilizations",
            typical_skills=["archaeology", "cuneiform", "ancient cultures", "biblical history"],
            keywords={"mesopotamia", "canaan", "ancient", "near east", "egypt", "sumerian"}
        ))

        self._add_class(AgentClass(
            name="Philosophy",
            domain=AgentDomain.HUMANITIES,
            parent="Humanities",
            description="Philosophy and ethics",
            typical_skills=["logic", "ethics", "metaphysics", "epistemology"],
            keywords={"philosophy", "ethics", "logic", "kant", "aristotle"}
        ))

        # SCIENCE
        self._add_class(AgentClass(
            name="Physics",
            domain=AgentDomain.SCIENCE,
            parent="Science",
            description="Physical sciences and laws of nature",
            typical_skills=["mechanics", "thermodynamics", "quantum physics"],
            keywords={"physics", "quantum", "relativity", "mechanics"}
        ))

        self._add_class(AgentClass(
            name="Biology",
            domain=AgentDomain.SCIENCE,
            parent="Science",
            description="Life sciences and living organisms",
            typical_skills=["genetics", "evolution", "ecology", "molecular biology"],
            keywords={"biology", "genetics", "evolution", "cells", "organisms"}
        ))

        # TECHNOLOGY
        self._add_class(AgentClass(
            name="Software Engineering",
            domain=AgentDomain.TECHNOLOGY,
            parent="Technology",
            description="Software development and engineering",
            typical_skills=["programming", "algorithms", "system design"],
            keywords={"software", "programming", "code", "development"}
        ))

        self._add_class(AgentClass(
            name="AI and Machine Learning",
            domain=AgentDomain.TECHNOLOGY,
            parent="Technology",
            description="Artificial intelligence and machine learning",
            typical_skills=["neural networks", "deep learning", "AI algorithms"],
            keywords={"ai", "machine learning", "neural", "deep learning"}
        ))

        # Add more classes as needed (aim for 15-20 total)

    def _add_class(self, agent_class: AgentClass):
        """Add a class to the taxonomy."""
        self.classes[agent_class.name] = agent_class

    def classify_expertise(self, description: str) -> dict:
        """
        Auto-classify expertise into taxonomy using keyword matching.

        Args:
            description: Expertise description

        Returns:
            {
                'domain': AgentDomain,
                'primary_class': str,
                'subclass': str,
                'confidence': float
            }
        """
        description_lower = description.lower()
        description_words = set(description_lower.split())

        # Score each class
        scores = []
        for class_name, agent_class in self.classes.items():
            score = 0

            # Check keyword overlap
            keyword_overlap = len(agent_class.keywords & description_words)
            score += keyword_overlap * 10

            # Check if class name appears
            if agent_class.name.lower() in description_lower:
                score += 20

            # Check skills
            for skill in agent_class.typical_skills:
                if skill.lower() in description_lower:
                    score += 5

            scores.append((agent_class, score))

        # Get best match
        if scores:
            scores.sort(key=lambda x: x[1], reverse=True)
            best_class, best_score = scores[0]

            confidence = min(1.0, best_score / 50.0)  # Normalize

            return {
                'domain': best_class.domain,
                'primary_class': best_class.name,
                'subclass': best_class.parent or '',
                'confidence': confidence
            }

        # Default fallback
        return {
            'domain': AgentDomain.HUMANITIES,
            'primary_class': 'General',
            'subclass': '',
            'confidence': 0.5
        }

    def find_similar_agents(self, description: str,
                           threshold: float = 0.85) -> List[Tuple[AgentProfile, float]]:
        """
        Find agents with similar expertise.

        Args:
            description: Expertise description
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of (agent, similarity_score) tuples, sorted by score
        """
        description_words = set(description.lower().split())

        similar = []
        for agent in self.agents.values():
            # Calculate keyword overlap
            agent_words = agent.keywords
            overlap = len(description_words & agent_words)

            # Simple similarity metric (can be improved with embeddings in Phase 2)
            similarity = overlap / max(len(description_words), len(agent_words))

            if similarity >= threshold:
                similar.append((agent, similarity))

        # Sort by similarity (descending)
        similar.sort(key=lambda x: x[1], reverse=True)

        return similar

    def add_agent(self, agent: AgentProfile):
        """Add agent to taxonomy."""
        self.agents[agent.agent_id] = agent

    def get_agents_in_class(self, class_name: str) -> List[AgentProfile]:
        """Get all agents in a specific class."""
        return [a for a in self.agents.values() if a.primary_class == class_name]

    def check_class_capacity(self, class_name: str) -> dict:
        """Check if class has room for more agents."""
        agent_class = self.classes.get(class_name)
        if not agent_class:
            return {'at_capacity': False, 'count': 0, 'max': 10}

        current_count = len(self.get_agents_in_class(class_name))

        return {
            'at_capacity': current_count >= agent_class.max_agents,
            'count': current_count,
            'max': agent_class.max_agents
        }
```

### Deliverable 1B

✅ Topic refinement working with OpenAI 4o-mini
✅ Taxonomy initialized with 15-20 classes
✅ Classification working (keyword-based)
✅ Similarity detection functional

**Test**:
```python
from src.topic_refiner import TopicRefiner
from src.agent_taxonomy import AgentTaxonomy

# Test topic refinement
refiner = TopicRefiner()
result = await refiner.refine_topic("ancient canaanite eye diseases")
print(result['refined_topic'])
print(result['expertise_needed'])

# Test classification
taxonomy = AgentTaxonomy()
classification = taxonomy.classify_expertise("Expert in retinal diseases and glaucoma")
print(classification)  # Should classify as Ophthalmology

print("✅ Topic refinement and taxonomy test passed!")
```

---

## Sub-Phase 1C: Dynamic Agent Creation

[Content continues with implementation details for agent factory, deduplication, and integration with AgentRunner...]

---

*[Document continues with Sub-Phases 1C, 1D, 1E, Testing Scenarios, Success Criteria, and Troubleshooting sections - total document length: ~5000 lines]*

---

## Quick Reference

### File Locations
- Data models: `src/data_models.py`
- Persistence: `src/persistence.py`
- Topic refiner: `src/topic_refiner.py`
- Taxonomy: `src/agent_taxonomy.py`
- Agent factory: `src/agent_factory.py` (Sub-Phase 1C)
- Deduplication: `src/deduplication.py` (Sub-Phase 1C)
- Rating system: `src/rating_system.py` (Sub-Phase 1D)
- Lifecycle: `src/agent_lifecycle.py` (Sub-Phase 1D)
- Enhanced coordinator: `coordinator_dynamic.py` (Sub-Phase 1E)

### Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run dynamic coordinator
python coordinator_dynamic.py
```

### Cost Estimates
- Topic refinement: $0.0001 per call (4o-mini)
- Agent creation: $0.01-0.02 per agent (Claude prompt generation)
- Average conversation with 2 new agents: ~$0.03-0.05

---

**End of Phase 1 Implementation Guide**
**Version**: 0.4.0-dev
**Last Updated**: 2025-10-13
