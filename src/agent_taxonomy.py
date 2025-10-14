"""
Agent classification and taxonomy system.
Organizes agents by Domain > Class > Specialization.

This module provides:
- 22 agent classes across 7 domains
- Classification based on keyword matching with API fallback
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

        # HUMANITIES (8 classes) - EXPANDED
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
            keywords={"language", "linguistics", "phonetics", "syntax", "grammar", "morphology", "mandarin", "chinese", "bilingual"}
        ))

        self._add_class(AgentClass(
            name="Cultural Studies",
            domain=AgentDomain.HUMANITIES,
            parent="Humanities",
            description="Cultural analysis and cross-cultural studies",
            typical_skills=["cultural analysis", "ethnography", "intercultural communication"],
            keywords={"culture", "cultural", "intercultural", "cross-cultural", "ethnography", "society", "tradition", "heritage"}
        ))

        self._add_class(AgentClass(
            name="History",
            domain=AgentDomain.HUMANITIES,
            parent="Humanities",
            description="General historical studies",
            typical_skills=["historical research", "historiography", "archival research"],
            keywords={"history", "historical", "historian", "past", "civilization", "era", "period"}
        ))

        self._add_class(AgentClass(
            name="Psychology",
            domain=AgentDomain.HUMANITIES,
            parent="Humanities",
            description="Human behavior and mental processes",
            typical_skills=["cognitive psychology", "behavioral analysis", "mental health", "therapy"],
            keywords={"psychology", "psychological", "cognitive", "behavioral", "mental", "therapy", "counseling"}
        ))

        self._add_class(AgentClass(
            name="Education",
            domain=AgentDomain.HUMANITIES,
            parent="Humanities",
            description="Teaching, learning, and pedagogy",
            typical_skills=["curriculum design", "pedagogy", "learning theory", "assessment"],
            keywords={"education", "teaching", "pedagogy", "curriculum", "learning", "classroom", "student", "instruction"}
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

        # Total: 22 classes across 7 domains (8 in HUMANITIES, 4 in MEDICINE, 4 in SCIENCE, 3 in TECHNOLOGY, 2 in BUSINESS, 1 in LAW, 2 in ARTS)

    def _add_class(self, agent_class: AgentClass):
        """Add a class to the taxonomy."""
        self.classes[agent_class.name] = agent_class

    def classify_expertise(self, description: str) -> dict:
        """
        Auto-classify expertise into taxonomy using keyword matching with API fallback.

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
        print(f"\n🔍 Classifying expertise: '{description}'")
        description_lower = description.lower()
        description_words = set(description_lower.split())

        # Try keyword-based classification first
        result = self._classify_by_keywords(description_lower, description_words)

        if result and result['confidence'] >= 0.3:
            print(f"   ✅ Keyword match: {result['primary_class']} ({result['domain'].value}) - confidence: {result['confidence']:.2f}")
            return result

        print(f"   ⚠️  Low confidence ({result['confidence']:.2f} if result else 0.0) - trying API classification...")

        # Fallback to API-based classification
        api_result = self._classify_via_api(description)
        if api_result:
            print(f"   ✅ API classification: {api_result['primary_class']} ({api_result['domain'].value})")
            return api_result

        print(f"   ❌ API classification failed - returning None")
        return None

    def _classify_by_keywords(self, description_lower: str, description_words: set) -> dict:
        """
        Classify expertise using comprehensive keyword matching rules.

        Returns classification dict or None if no good match found.
        """
        # Extensive keyword-based classification rules
        # NOTE: Order matters! More specific checks should come FIRST

        # TECHNOLOGY - Check AI/ML before "learning" keyword
        if any(phrase in description_lower for phrase in ['machine learning', 'deep learning', 'artificial intelligence', 'neural network']):
            print(f"      → AI/ML keywords found")
            return {
                'domain': AgentDomain.TECHNOLOGY,
                'primary_class': 'AI and Machine Learning',
                'subclass': 'Technology',
                'confidence': 0.9
            }

        if any(word in description_lower for word in ['software', 'programming', 'code', 'developer', 'engineering']):
            print(f"      → Software Engineering keywords found")
            return {
                'domain': AgentDomain.TECHNOLOGY,
                'primary_class': 'Software Engineering',
                'subclass': 'Technology',
                'confidence': 0.9
            }

        # LINGUISTICS - Check before Education/Cultural (since they may share keywords)
        if any(word in description_lower for word in ['mandarin', 'cantonese', 'bilingual', 'multilingual']):
            print(f"      → Linguistics keywords found (language/bilingual)")
            return {
                'domain': AgentDomain.HUMANITIES,
                'primary_class': 'Linguistics',
                'subclass': 'Humanities',
                'confidence': 0.9
            }

        # Check for "language learning" or "chinese language" as phrases
        if 'language learning' in description_lower or 'chinese language' in description_lower or 'language teaching' in description_lower:
            print(f"      → Linguistics keywords found (language learning/teaching)")
            return {
                'domain': AgentDomain.HUMANITIES,
                'primary_class': 'Linguistics',
                'subclass': 'Humanities',
                'confidence': 0.9
            }

        if any(word in description_lower for word in ['linguistics', 'phonetics', 'syntax', 'grammar', 'morphology', 'language structure']):
            print(f"      → Linguistics keywords found (technical)")
            return {
                'domain': AgentDomain.HUMANITIES,
                'primary_class': 'Linguistics',
                'subclass': 'Humanities',
                'confidence': 0.9
            }

        # CULTURAL STUDIES - Check before "chinese" alone triggers something else
        if any(word in description_lower for word in ['cultural', 'culture', 'intercultural', 'cross-cultural', 'ethnography', 'anthropology']):
            # But NOT if it's about language teaching (already handled above)
            if 'language' not in description_lower or 'cultural' in description_lower:
                print(f"      → Cultural Studies keywords found")
                return {
                    'domain': AgentDomain.HUMANITIES,
                    'primary_class': 'Cultural Studies',
                    'subclass': 'Humanities',
                    'confidence': 0.85
                }

        # EDUCATION - Check after Linguistics/Cultural to avoid false matches
        if any(word in description_lower for word in ['pedagogy', 'curriculum', 'education', 'classroom']):
            print(f"      → Education keywords found")
            return {
                'domain': AgentDomain.HUMANITIES,
                'primary_class': 'Education',
                'subclass': 'Humanities',
                'confidence': 0.85
            }

        # "teaching" alone could be Education OR Linguistics, check context
        if 'teaching' in description_lower:
            # If it's about teaching a language, it's Linguistics
            if any(word in description_lower for word in ['language', 'mandarin', 'chinese', 'english', 'spanish', 'french']):
                print(f"      → Linguistics keywords found (language teaching)")
                return {
                    'domain': AgentDomain.HUMANITIES,
                    'primary_class': 'Linguistics',
                    'subclass': 'Humanities',
                    'confidence': 0.85
                }
            # Otherwise it's Education
            print(f"      → Education keywords found (teaching)")
            return {
                'domain': AgentDomain.HUMANITIES,
                'primary_class': 'Education',
                'subclass': 'Humanities',
                'confidence': 0.8
            }

        # PSYCHOLOGY
        if any(word in description_lower for word in ['psychology', 'psychological', 'cognitive', 'behavioral', 'mental health', 'therapy']):
            print(f"      → Psychology keywords found")
            return {
                'domain': AgentDomain.HUMANITIES,
                'primary_class': 'Psychology',
                'subclass': 'Humanities',
                'confidence': 0.9
            }

        # HISTORY
        if any(word in description_lower for word in ['history', 'historical', 'historian', 'past', 'civilization', 'era', 'period', 'ancient']):
            print(f"      → History keywords found")
            return {
                'domain': AgentDomain.HUMANITIES,
                'primary_class': 'History',
                'subclass': 'Humanities',
                'confidence': 0.85
            }

        # MEDICINE (only if explicitly medical)
        if any(word in description_lower for word in ['medical', 'medicine', 'doctor', 'physician', 'clinical', 'patient', 'disease', 'treatment']):
            # Check for specific medical specialties
            if any(word in description_lower for word in ['heart', 'cardiac', 'cardiovascular', 'cardiology']):
                print(f"      → Cardiology keywords found")
                return {
                    'domain': AgentDomain.MEDICINE,
                    'primary_class': 'Cardiology',
                    'subclass': 'Medicine',
                    'confidence': 0.9
                }
            elif any(word in description_lower for word in ['brain', 'neural', 'neurology', 'nervous', 'neurological']):
                print(f"      → Neurology keywords found")
                return {
                    'domain': AgentDomain.MEDICINE,
                    'primary_class': 'Neurology',
                    'subclass': 'Medicine',
                    'confidence': 0.9
                }
            elif any(word in description_lower for word in ['eye', 'vision', 'ophthalmology', 'retina', 'ocular']):
                print(f"      → Ophthalmology keywords found")
                return {
                    'domain': AgentDomain.MEDICINE,
                    'primary_class': 'Ophthalmology',
                    'subclass': 'Medicine',
                    'confidence': 0.9
                }
            elif any(word in description_lower for word in ['cancer', 'oncology', 'tumor', 'chemotherapy']):
                print(f"      → Oncology keywords found")
                return {
                    'domain': AgentDomain.MEDICINE,
                    'primary_class': 'Oncology',
                    'subclass': 'Medicine',
                    'confidence': 0.9
                }

        # BIOLOGY
        if any(word in description_lower for word in ['biology', 'genetics', 'evolution', 'cells', 'organisms', 'ecology', 'dna']):
            print(f"      → Biology keywords found")
            return {
                'domain': AgentDomain.SCIENCE,
                'primary_class': 'Biology',
                'subclass': 'Science',
                'confidence': 0.9
            }

        # Fallback: Score each class
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

            if score > 0:
                scores.append((agent_class, score))

        # Get best match only if score is meaningful
        if scores:
            scores.sort(key=lambda x: x[1], reverse=True)
            best_class, best_score = scores[0]

            # Only return if confidence is reasonable
            confidence = min(1.0, best_score / 50.0)

            if confidence >= 0.3:
                print(f"      → Fallback scoring: {best_class.name} (score: {best_score}, confidence: {confidence:.2f})")
                return {
                    'domain': best_class.domain,
                    'primary_class': best_class.name,
                    'subclass': best_class.parent or '',
                    'confidence': confidence
                }

        print(f"      → No good keyword match found")
        return None

    def _classify_via_api(self, description: str) -> dict:
        """
        Use Claude API to classify ambiguous expertise descriptions.

        Returns classification dict or None if API call fails.
        """
        try:
            import anthropic
            import os

            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print(f"      ⚠️  No Anthropic API key found")
                return None

            client = anthropic.Anthropic(api_key=api_key)

            # Build list of available classes
            classes_list = []
            for class_name, agent_class in self.classes.items():
                classes_list.append(f"- {class_name} ({agent_class.domain.value}): {agent_class.description}")

            prompt = f"""Given this expertise description:
"{description}"

Classify it into ONE of these classes:
{chr(10).join(classes_list)}

Respond with ONLY the class name (e.g., "Linguistics", "Cultural Studies", "History", etc.).
If none fit well, respond with "NONE".
"""

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )

            classification = response.content[0].text.strip()

            if classification == "NONE" or classification not in self.classes:
                print(f"      ⚠️  API returned: {classification}")
                return None

            agent_class = self.classes[classification]
            return {
                'domain': agent_class.domain,
                'primary_class': agent_class.name,
                'subclass': agent_class.parent or '',
                'confidence': 0.75  # API-based gets medium-high confidence
            }

        except Exception as e:
            print(f"      ❌ API classification error: {e}")
            return None

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
