"""
Agent classification and taxonomy system.
Organizes agents by Domain > Class > Specialization.

This module provides:
- 20 agent classes across 7 domains
- Classification based on keyword matching
- Similarity detection for deduplication
- Capacity management per class
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
        """Create taxonomy tree with 20 classes across 7 domains."""

        # MEDICINE (4 classes)
        self._add_class(AgentClass(
            name="Cardiology",
            domain=AgentDomain.MEDICINE,
            parent="Medicine",
            description="Heart and cardiovascular system",
            typical_skills=["cardiac care", "heart disease", "interventional cardiology"],
            keywords={"heart", "cardiac", "cardiovascular", "cardiology", "coronary"}
        ))

        self._add_class(AgentClass(
            name="Neurology",
            domain=AgentDomain.MEDICINE,
            parent="Medicine",
            description="Brain and nervous system",
            typical_skills=["neurological disorders", "brain", "neuroscience"],
            keywords={"brain", "neural", "neurology", "nervous", "neurological"}
        ))

        self._add_class(AgentClass(
            name="Ophthalmology",
            domain=AgentDomain.MEDICINE,
            parent="Medicine",
            description="Eye diseases and vision",
            typical_skills=["retinal diseases", "glaucoma", "cataracts", "vision"],
            keywords={"eye", "vision", "ophthalmology", "retina", "visual", "ocular"}
        ))

        self._add_class(AgentClass(
            name="Oncology",
            domain=AgentDomain.MEDICINE,
            parent="Medicine",
            description="Cancer treatment and research",
            typical_skills=["cancer treatment", "chemotherapy", "tumor biology"],
            keywords={"cancer", "oncology", "tumor", "chemotherapy", "malignancy"}
        ))

        # HUMANITIES (4 classes)
        self._add_class(AgentClass(
            name="Ancient Near East",
            domain=AgentDomain.HUMANITIES,
            parent="Ancient History",
            description="Mesopotamia, Canaan, Egypt, ancient civilizations",
            typical_skills=["archaeology", "cuneiform", "ancient cultures", "biblical history"],
            keywords={"mesopotamia", "canaan", "ancient", "near east", "egypt", "sumerian", "babylonian"}
        ))

        self._add_class(AgentClass(
            name="Philosophy",
            domain=AgentDomain.HUMANITIES,
            parent="Humanities",
            description="Philosophy and ethics",
            typical_skills=["logic", "ethics", "metaphysics", "epistemology"],
            keywords={"philosophy", "ethics", "logic", "kant", "aristotle", "metaphysics"}
        ))

        self._add_class(AgentClass(
            name="Classical History",
            domain=AgentDomain.HUMANITIES,
            parent="Ancient History",
            description="Greek and Roman civilizations",
            typical_skills=["classical archaeology", "latin", "greek", "roman history"],
            keywords={"rome", "roman", "greece", "greek", "classical", "ancient"}
        ))

        self._add_class(AgentClass(
            name="Linguistics",
            domain=AgentDomain.HUMANITIES,
            parent="Humanities",
            description="Language structure and evolution",
            typical_skills=["phonetics", "syntax", "semantics", "language families"],
            keywords={"language", "linguistics", "phonetics", "syntax", "grammar", "morphology"}
        ))

        # SCIENCE (4 classes)
        self._add_class(AgentClass(
            name="Physics",
            domain=AgentDomain.SCIENCE,
            parent="Science",
            description="Physical sciences and laws of nature",
            typical_skills=["mechanics", "thermodynamics", "quantum physics"],
            keywords={"physics", "quantum", "relativity", "mechanics", "thermodynamics"}
        ))

        self._add_class(AgentClass(
            name="Biology",
            domain=AgentDomain.SCIENCE,
            parent="Science",
            description="Life sciences and living organisms",
            typical_skills=["genetics", "evolution", "ecology", "molecular biology"],
            keywords={"biology", "genetics", "evolution", "cells", "organisms", "ecology"}
        ))

        self._add_class(AgentClass(
            name="Chemistry",
            domain=AgentDomain.SCIENCE,
            parent="Science",
            description="Matter, composition, and chemical reactions",
            typical_skills=["organic chemistry", "inorganic chemistry", "reactions"],
            keywords={"chemistry", "chemical", "molecules", "reactions", "compounds"}
        ))

        self._add_class(AgentClass(
            name="Astronomy",
            domain=AgentDomain.SCIENCE,
            parent="Science",
            description="Celestial objects and phenomena",
            typical_skills=["astrophysics", "cosmology", "planetary science"],
            keywords={"astronomy", "astrophysics", "stars", "planets", "cosmology", "universe"}
        ))

        # TECHNOLOGY (3 classes)
        self._add_class(AgentClass(
            name="Software Engineering",
            domain=AgentDomain.TECHNOLOGY,
            parent="Technology",
            description="Software development and engineering",
            typical_skills=["programming", "algorithms", "system design"],
            keywords={"software", "programming", "code", "development", "engineering"}
        ))

        self._add_class(AgentClass(
            name="AI and Machine Learning",
            domain=AgentDomain.TECHNOLOGY,
            parent="Technology",
            description="Artificial intelligence and machine learning",
            typical_skills=["neural networks", "deep learning", "AI algorithms"],
            keywords={"ai", "machine learning", "neural", "deep learning", "artificial intelligence"}
        ))

        self._add_class(AgentClass(
            name="Cybersecurity",
            domain=AgentDomain.TECHNOLOGY,
            parent="Technology",
            description="Information security and cryptography",
            typical_skills=["network security", "cryptography", "penetration testing"],
            keywords={"security", "cybersecurity", "cryptography", "encryption", "hacking"}
        ))

        # BUSINESS (2 classes)
        self._add_class(AgentClass(
            name="Finance",
            domain=AgentDomain.BUSINESS,
            parent="Business",
            description="Financial markets and investment",
            typical_skills=["financial analysis", "investment", "portfolio management"],
            keywords={"finance", "investment", "stocks", "bonds", "trading", "market"}
        ))

        self._add_class(AgentClass(
            name="Management",
            domain=AgentDomain.BUSINESS,
            parent="Business",
            description="Business strategy and operations",
            typical_skills=["strategic planning", "operations", "leadership"],
            keywords={"management", "strategy", "operations", "business", "leadership"}
        ))

        # LAW (1 class)
        self._add_class(AgentClass(
            name="Constitutional Law",
            domain=AgentDomain.LAW,
            parent="Law",
            description="Constitutional principles and interpretation",
            typical_skills=["constitutional analysis", "legal precedent", "judicial review"],
            keywords={"law", "legal", "constitution", "judicial", "precedent", "court"}
        ))

        # ARTS (2 classes)
        self._add_class(AgentClass(
            name="Visual Arts",
            domain=AgentDomain.ARTS,
            parent="Arts",
            description="Painting, sculpture, and visual media",
            typical_skills=["art history", "painting", "sculpture", "design"],
            keywords={"art", "painting", "sculpture", "visual", "design", "artist"}
        ))

        self._add_class(AgentClass(
            name="Music",
            domain=AgentDomain.ARTS,
            parent="Arts",
            description="Music theory, composition, and performance",
            typical_skills=["music theory", "composition", "performance", "harmony"],
            keywords={"music", "musical", "composition", "harmony", "melody", "song"}
        ))

        # Total: 20 classes across 7 domains

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

    def get_all_classes(self) -> List[AgentClass]:
        """Get all agent classes."""
        return list(self.classes.values())

    def get_classes_by_domain(self, domain: AgentDomain) -> List[AgentClass]:
        """Get all classes in a specific domain."""
        return [c for c in self.classes.values() if c.domain == domain]

    def get_class_count(self) -> int:
        """Get total number of classes in taxonomy."""
        return len(self.classes)
