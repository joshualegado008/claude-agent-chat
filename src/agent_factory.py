"""
Agent Factory - Creates agents dynamically using Claude API

This module provides the AgentFactory class which creates complete agent profiles
by leveraging Claude Sonnet 4.5 for generating:
- Realistic names with appropriate titles
- Comprehensive system prompts (200-500 words)
- Core skills and keywords
- Personality traits

Cost tracking is built-in to monitor API usage.
"""

import os
import uuid
import json
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Set
from datetime import datetime
import anthropic
from dotenv import load_dotenv
import numpy as np

from src.data_models import AgentProfile, AgentDomain

load_dotenv()


class AgentFactory:
    """Creates agents dynamically from expertise descriptions."""

    # Claude Sonnet 4.5 pricing (as of 2025-10-13)
    INPUT_COST_PER_MTOK = 3.0   # $3 per million tokens
    OUTPUT_COST_PER_MTOK = 15.0  # $15 per million tokens

    def __init__(self, taxonomy=None):
        """
        Initialize the agent factory.

        Args:
            taxonomy: AgentTaxonomy instance for classification
        """
        self.taxonomy = taxonomy

        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"

        # Setup dynamic agents directory
        self.agents_dir = Path(".claude/agents/dynamic")
        self.agents_dir.mkdir(parents=True, exist_ok=True)

        # Cost tracking
        self.total_creation_cost = 0.0
        self.agents_created = 0

        # Name uniqueness tracking (to prevent duplicate names)
        self.used_names: Set[str] = set()
        self._name_lock = asyncio.Lock()

        # Load existing agent names from disk
        self._load_existing_names()

    def _load_existing_names(self) -> None:
        """
        Load existing agent names from disk to prevent duplicates.

        Scans the dynamic agents directory and extracts names from
        agent metadata files or markdown headers.
        """
        if not self.agents_dir.exists():
            return

        # Scan all .md files in dynamic agents directory
        for agent_file in self.agents_dir.glob("*.md"):
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract name from first markdown header
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        # Extract name (e.g., "# Dr. Jane Smith - Expert in X")
                        name = line[2:].split(' - ')[0].strip()
                        self.used_names.add(name)
                        break

            except Exception as e:
                print(f"   ⚠️  Warning: Failed to read {agent_file.name}: {e}")

        # Count total files for more informative message
        total_files = len(list(self.agents_dir.glob("*.md")))

        if self.used_names:
            if total_files == len(self.used_names):
                # All files have unique names
                print(f"   📝 Loaded {len(self.used_names)} existing agents")
            else:
                # Some duplicates exist (shouldn't happen after cleanup, but defensive)
                duplicates = total_files - len(self.used_names)
                print(f"   📝 Loaded {len(self.used_names)} unique agents ({total_files} files, {duplicates} duplicates detected)")

    def _generate_unique_name_with_faker(self, domain: AgentDomain, classification: Dict) -> Optional[str]:
        """
        Generate diverse, unique agent names using faker library.

        This method dramatically reduces duplicate name collisions by:
        - Using faker's extensive name database (1000+ names per locale)
        - Trying multiple locales for diversity
        - Applying domain-specific title logic
        - Checking uniqueness before returning

        Args:
            domain: Agent's domain (TECHNOLOGY, MEDICINE, etc.)
            classification: Classification dict with domain/class info

        Returns:
            Unique name with optional title (e.g., "Sarah Kim" or "Dr. James Rodriguez")
            Returns None if faker fails (triggers Claude API fallback)
        """
        try:
            from faker import Faker
            import random

            # Domain-specific title configuration
            # Target: ~30% overall title usage, varied by domain
            TITLE_CONFIG = {
                'TECHNOLOGY': {
                    'titles': ['', '', '', '', 'Engineer', 'Researcher', 'Architect'],
                    'probability': 0.2  # 20% get titles
                },
                'MEDICINE': {
                    'titles': ['Dr.', 'Dr.', 'Nurse', 'Practitioner', '', ''],
                    'probability': 0.5  # 50% get titles (medical field)
                },
                'HUMANITIES': {
                    'titles': ['Prof.', 'Dr.', '', '', ''],
                    'probability': 0.4  # 40% get titles (academic)
                },
                'SCIENCE': {
                    'titles': ['Dr.', 'Prof.', 'Researcher', '', ''],
                    'probability': 0.4  # 40% get titles
                },
                'BUSINESS': {
                    'titles': ['', '', '', 'CTO', 'CEO', 'VP', 'Analyst'],
                    'probability': 0.25  # 25% get titles
                },
                'LAW': {
                    'titles': ['Attorney', 'Esq.', '', ''],
                    'probability': 0.35  # 35% get titles
                },
                'ARTS': {
                    'titles': ['', '', '', '', 'Maestro', 'Designer'],
                    'probability': 0.15  # 15% get titles (mostly informal)
                }
            }

            # Diverse locales for cultural variety
            # Rotate through different regions to avoid clustering
            locales = [
                'en_US',   # American names
                'en_GB',   # British names
                'es_ES',   # Spanish names
                'fr_FR',   # French names
                'de_DE',   # German names
                'it_IT',   # Italian names
                'zh_CN',   # Chinese names
                'ja_JP',   # Japanese names
                'ko_KR',   # Korean names
                'pt_BR',   # Brazilian names
                'pl_PL',   # Polish names
                'nl_NL',   # Dutch names
                'sv_SE'    # Swedish names
            ]

            # Try up to 10 different combinations before giving up
            for attempt in range(10):
                # Pick locale (rotate through list for max diversity)
                locale = locales[attempt % len(locales)]
                fake = Faker(locale)

                # Generate base name (faker handles cultural appropriateness)
                base_name = fake.name()

                # Check if name is already used
                if base_name in self.used_names:
                    continue  # Try next locale

                # Apply domain-specific title logic
                domain_rules = TITLE_CONFIG.get(
                    domain.name,
                    {'probability': 0.3, 'titles': ['', '', 'Dr.']}  # Default fallback
                )

                final_name = base_name

                # Roll dice for title (based on domain probability)
                if random.random() < domain_rules['probability']:
                    title = random.choice(domain_rules['titles'])
                    if title:  # Empty string means no title
                        final_name = f"{title} {base_name}"

                # Final uniqueness check (in case title made it duplicate)
                if final_name not in self.used_names:
                    return final_name

            # If we exhausted all attempts, return None (triggers Claude fallback)
            print(f"   ⚠️  Faker couldn't generate unique name after 10 attempts")
            return None

        except Exception as e:
            print(f"   ⚠️  Faker library error: {e}")
            return None

    async def create_agent(
        self,
        expertise_description: str,
        classification: Optional[Dict] = None,
        context: Optional[str] = None,
        created_by: str = "system"
    ) -> AgentProfile:
        """
        Create complete agent from expertise description.

        Process:
        1. Classify expertise (if not provided)
        2. Generate agent details (name, skills, keywords) via Claude
        3. Generate system prompt via Claude
        4. Create AgentProfile
        5. Generate embedding (hash-based for Phase 1)
        6. Write agent file
        7. Return profile

        Args:
            expertise_description: Description of required expertise
            classification: Optional pre-computed classification
            context: Optional additional context for agent creation
            created_by: Creator identifier (default: "system")

        Returns:
            Complete AgentProfile instance

        Raises:
            ValueError: If classification fails or API errors occur
        """
        print(f"🔮 Creating agent for: {expertise_description[:60]}...")

        # Step 1: Classify expertise
        if not classification:
            if not self.taxonomy:
                raise ValueError("Taxonomy required for classification")
            classification = self.taxonomy.classify_expertise(expertise_description)
            if not classification:
                # Use generic fallback classification
                print(f"   ⚠️  Classification failed - using generic HUMANITIES classification")
                classification = {
                    'domain': AgentDomain.HUMANITIES,
                    'primary_class': 'General Studies',
                    'subclass': 'Humanities',
                    'confidence': 0.0
                }

        domain = classification['domain']
        primary_class = classification['primary_class']
        subclass = classification.get('subclass', '')

        print(f"   └─ Classified as: {primary_class} ({domain.value})")

        # Step 2: Generate unique name using faker library (pre-Claude)
        generated_name = None
        try:
            generated_name = self._generate_unique_name_with_faker(domain, classification)
            if generated_name:
                print(f"   └─ Name generated: {generated_name}")
                # Pass name to Claude via context
                name_context = f"Agent name (use exactly): {generated_name}"
                if context:
                    context = f"{name_context}\n{context}"
                else:
                    context = name_context
            else:
                print(f"   └─ Name generation: Using Claude API fallback")
        except Exception as e:
            print(f"   ⚠️  Faker failed ({e}), using Claude API")

        # Step 3: Generate agent details using Claude API (with uniqueness check)
        try:
            agent_details = await self._generate_agent_details(
                expertise_description,
                classification,
                context
            )
            print(f"   └─ Generated: {agent_details['name']}")

            # Defensive check: name should already be registered in _generate_agent_details
            # This is a safety net in case of errors
            async with self._name_lock:
                if agent_details['name'] not in self.used_names:
                    print(f"   ⚠️  Warning: Name not registered, adding now (shouldn't happen)")
                    self.used_names.add(agent_details['name'])

        except Exception as e:
            print(f"   ❌ Failed to generate details: {e}")
            raise

        # Step 3: Generate system prompt using Claude API
        try:
            system_prompt = await self._generate_system_prompt(
                agent_details,
                classification,
                expertise_description
            )
            print(f"   └─ System prompt: {len(system_prompt.split())} words")
        except Exception as e:
            print(f"   ❌ Failed to generate prompt: {e}")
            raise

        # Step 3.5: Extract intelligent specialization (Three-Tier Taxonomy)
        try:
            specialization = await self._extract_specialization(
                expertise_description,
                primary_class
            )
            print(f"   └─ Specialization: {specialization}")
        except Exception as e:
            # Fallback to truncation if extraction fails
            specialization = expertise_description[:60].strip()
            print(f"   ⚠️  Using fallback specialization: {specialization}")

        # Step 4: Create AgentProfile
        agent_id = f"dynamic-{uuid.uuid4().hex[:12]}"
        agent_file_path = str(self.agents_dir / f"{agent_id}.md")

        # Generate hash-based embedding (simple for Phase 1)
        embedding = self._generate_hash_embedding(expertise_description)

        agent = AgentProfile(
            agent_id=agent_id,
            name=agent_details['name'],
            domain=domain,
            primary_class=primary_class,
            subclass=subclass,
            specialization=specialization,
            unique_expertise=expertise_description,
            core_skills=agent_details['core_skills'],
            keywords=set(agent_details['keywords']),
            system_prompt=system_prompt,
            created_at=datetime.now(),
            last_used=datetime.now(),
            agent_file_path=agent_file_path,
            total_uses=0,
            creation_cost_usd=agent_details['creation_cost'],
            created_by=created_by,
            model=self.model,
            secondary_skills=agent_details.get('secondary_skills', []),
            expertise_embedding=embedding
        )

        # Step 5: Write agent file
        try:
            self._write_agent_file(agent)
            print(f"   └─ File written: {agent_file_path}")
        except Exception as e:
            print(f"   ⚠️  Warning: Failed to write file: {e}")

        # Update statistics
        self.agents_created += 1
        self.total_creation_cost += agent_details['creation_cost']

        print(f"   ✅ Agent created! Cost: ${agent_details['creation_cost']:.4f}")

        return agent

    async def _generate_agent_details(
        self,
        expertise_description: str,
        classification: Dict,
        context: Optional[str] = None
    ) -> Dict:
        """
        Generate agent details using Claude API with uniqueness checking.

        Retries up to 3 times if a duplicate name is generated.

        Returns dict with:
        - name: Agent name with appropriate title (guaranteed unique)
        - core_skills: List of 3-5 skills
        - keywords: List of 5-8 keywords
        - personality_traits: List of 2-3 traits
        - secondary_skills: Additional skills
        - creation_cost: Cost of this API call
        """
        domain = classification['domain'].value
        primary_class = classification['primary_class']

        max_retries = 3
        for attempt in range(max_retries):
            # Check for duplicate names and adjust prompt
            avoid_names = ""
            if attempt > 0:
                async with self._name_lock:
                    recent_names = list(self.used_names)[-10:]  # Last 10 names
                avoid_names = f"\n\n**IMPORTANT**: These names are already taken, choose a DIFFERENT name:\n{', '.join(recent_names)}"

            prompt = f"""Create a detailed agent profile for a specialist with this expertise:

**Expertise**: {expertise_description}
**Domain**: {domain}
**Classification**: {primary_class}
{f"**Context**: {context}" if context else ""}{avoid_names}

Generate a complete agent profile with the following:

1. **Name**: If a name is provided in context, USE IT EXACTLY AS GIVEN. Otherwise, create a realistic name.
   - Prefer NO TITLE for most agents (makes roster more approachable)
   - Only use titles (Dr., Prof., Engineer) if absolutely fitting for the domain
   - Technology/Business: Avoid titles (just "FirstName LastName")
   - Academic fields: Occasional "Prof." or "Dr." is acceptable

2. **Core Skills**: List 3-5 specific, concrete skills this agent excels at

3. **Keywords**: List 5-8 relevant keywords for this expertise (lowercase, single words or short phrases)

4. **Personality Traits**: List 2-3 personality traits that fit this expertise

5. **Secondary Skills**: List 2-3 additional complementary skills

Return ONLY a JSON object with this exact structure:
{{
  "name": "Dr. Jane Smith",
  "core_skills": ["skill1", "skill2", "skill3"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "personality_traits": ["trait1", "trait2"],
  "secondary_skills": ["skill1", "skill2"]
}}

Be creative but realistic. The name should sound like a real expert in this field."""

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.8,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                # Extract usage and calculate cost
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._calculate_cost(input_tokens, output_tokens)

                # Parse JSON response
                content = response.content[0].text.strip()

                # Handle markdown code blocks if present
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()

                details = json.loads(content)
                details['creation_cost'] = cost

                # Check for name uniqueness (with lock)
                async with self._name_lock:
                    generated_name = details['name']
                    if generated_name in self.used_names:
                        if attempt < max_retries - 1:
                            print(f"      ⚠️  Duplicate name '{generated_name}' - retrying (attempt {attempt + 2}/{max_retries})")
                            continue  # Retry with updated prompt
                        else:
                            # Last attempt: append number to make unique
                            counter = 2
                            unique_name = f"{generated_name} {counter}"
                            while unique_name in self.used_names:
                                counter += 1
                                unique_name = f"{generated_name} {counter}"
                            details['name'] = unique_name
                            print(f"      ⚠️  Duplicate name - using '{unique_name}'")

                    # Register name immediately to prevent race conditions
                    # This must happen inside the lock before returning
                    self.used_names.add(details['name'])

                return details

            except json.JSONDecodeError as e:
                print(f"   ⚠️  JSON parse error: {e}")
                print(f"   Response: {content[:200]}")
                # Fallback details
                return self._generate_fallback_details(expertise_description, cost)
            except Exception as e:
                print(f"   ⚠️  API error: {e}")
                # Fallback with zero cost
                if attempt < max_retries - 1:
                    continue  # Retry
                return self._generate_fallback_details(expertise_description, 0.0)

        # Should never reach here, but just in case
        return self._generate_fallback_details(expertise_description, 0.0)

    async def _generate_system_prompt(
        self,
        agent_details: Dict,
        classification: Dict,
        expertise_description: str
    ) -> str:
        """
        Generate comprehensive system prompt using Claude API.

        Target: 200-500 words
        Style: Match existing agent_a.md format

        Returns:
            Complete system prompt as markdown string
        """
        domain = classification['domain'].value
        primary_class = classification['primary_class']
        name = agent_details['name']
        skills = ", ".join(agent_details['core_skills'][:3])
        traits = ", ".join(agent_details.get('personality_traits', ['professional', 'knowledgeable']))

        prompt = f"""Create a comprehensive system prompt for an AI agent with this profile:

**Name**: {name}
**Expertise**: {expertise_description}
**Domain**: {domain}
**Classification**: {primary_class}
**Core Skills**: {skills}
**Personality Traits**: {traits}

The system prompt should be 200-500 words and follow this structure (use markdown):

# [Agent Name] - [Brief Title]

[Opening paragraph introducing the agent and their expertise]

## Personality
- [3-5 bullet points describing personality traits]
- [Focus on how they approach problems and interact]

## Conversation Style
- [3-5 bullet points about communication style]
- [How they structure responses]
- [How they engage with other agents]

## Your Role
[Paragraph explaining their role in multi-agent discussions, emphasizing collaboration]

## Expertise Areas
[Paragraph highlighting specific areas of deep knowledge]

Remember: You're having a conversation with other AI agents. Be genuine, professional, and collaborative.

**Style Requirements**:
- Professional but engaging tone
- Emphasize collaboration with other agents
- Avoid being overly formal or robotic
- Keep responses concise (2-4 sentences per turn)
- Focus on adding unique value from this expertise

Generate the complete system prompt now. Use markdown formatting. Be specific about this agent's unique expertise."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Update creation cost (add to agent's total)
            agent_details['creation_cost'] = agent_details.get('creation_cost', 0.0) + cost

            system_prompt = response.content[0].text.strip()

            # Validate length (200-500 words target, but accept 150-600)
            word_count = len(system_prompt.split())
            if word_count < 150:
                print(f"   ⚠️  Prompt too short ({word_count} words), using fallback")
                return self._generate_fallback_prompt(agent_details, expertise_description)

            return system_prompt

        except Exception as e:
            print(f"   ⚠️  Prompt generation error: {e}")
            return self._generate_fallback_prompt(agent_details, expertise_description)

    async def _extract_specialization(
        self,
        expertise_description: str,
        primary_class: str
    ) -> str:
        """
        Extract concise specialization from expertise description using Claude API.

        This implements the third tier of the taxonomy hierarchy:
        Domain > Class > Specialization

        Args:
            expertise_description: Full expertise description
            primary_class: The agent's primary class (e.g., "Cybersecurity", "AI and Machine Learning")

        Returns:
            Concise specialization phrase (2-8 words)

        Examples:
            - "Quantum machine learning algorithms" → "Quantum ML"
            - "LLM jailbreaking and context poisoning" → "LLM Security"
            - "Byzantine taxation systems 400-1200 CE" → "Byzantine Taxation"
        """
        # Smart fallback: extract first 60 chars as baseline
        fallback = expertise_description[:60].strip()

        prompt = f"""Given this expertise description:
"{expertise_description}"

And the primary classification: {primary_class}

Extract a concise specialization (2-8 words) that captures the unique focus within this class.

Guidelines:
- Be specific but concise
- Avoid redundancy with the class name
- Focus on what makes THIS agent special within the class
- Use technical terms when appropriate
- Remove generic words like "expert in", "specialist in"

Examples:
- "Expert in quantum machine learning algorithms" → "Quantum ML"
- "LLM jailbreaking and context poisoning techniques" → "LLM Security"
- "Byzantine taxation systems from 400-1200 CE" → "Byzantine Taxation"
- "React component performance optimization" → "React Performance"

Return ONLY the specialization phrase (no quotes, no explanation)."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=30,
                temperature=0.3,  # Lower temperature for consistency
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            specialization = response.content[0].text.strip().strip('"\'')

            # Validate length (should be 2-8 words, but accept up to 12)
            word_count = len(specialization.split())
            if 2 <= word_count <= 12 and len(specialization) <= 80:
                return specialization
            else:
                print(f"   ⚠️  Specialization too long ({word_count} words), using fallback")
                return fallback

        except Exception as e:
            print(f"   ⚠️  Specialization extraction error: {e}, using fallback")
            return fallback

    def _write_agent_file(self, agent: AgentProfile) -> None:
        """
        Write agent markdown file to disk.

        Format matches existing agent_a.md structure.
        """
        content = agent.system_prompt

        # Add metadata footer
        content += f"\n\n---\n\n"
        content += f"**Agent ID**: {agent.agent_id}\n"
        content += f"**Domain**: {agent.domain.icon} {agent.domain.value.title()}\n"
        content += f"**Classification**: {agent.primary_class}\n"
        content += f"**Created**: {agent.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        content += f"**Model**: {agent.model}\n"

        # Write to file
        file_path = Path(agent.agent_file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_hash_embedding(self, text: str) -> np.ndarray:
        """
        Generate simple hash-based embedding for Phase 1.

        This is deterministic and fast. Phase 2 will use real embeddings
        from OpenAI's text-embedding-3-small model.

        Returns:
            128-dimensional numpy array
        """
        # Normalize text
        normalized = text.lower().strip()

        # Generate multiple hashes for different dimensions
        embedding = []
        for i in range(4):  # 4 iterations * 32 = 128 dimensions
            hash_input = f"{normalized}_{i}".encode('utf-8')
            hash_obj = hashlib.sha256(hash_input)
            hash_bytes = hash_obj.digest()

            # Convert bytes to 32 floats between -1 and 1
            for j in range(0, 32):
                if j < len(hash_bytes):
                    # Normalize byte (0-255) to (-1, 1)
                    value = (hash_bytes[j] / 255.0) * 2 - 1
                    embedding.append(value)
                else:
                    embedding.append(0.0)

        return np.array(embedding[:128])  # Ensure exactly 128 dimensions

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost of API call based on token usage.

        Claude Sonnet 4.5 pricing:
        - Input: $3 per million tokens
        - Output: $15 per million tokens
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_MTOK
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_MTOK
        return input_cost + output_cost

    def _generate_fallback_details(self, expertise_description: str, cost: float) -> Dict:
        """Generate fallback details if API fails."""
        # Extract keywords from description
        words = expertise_description.lower().split()
        keywords = [w for w in words if len(w) > 3][:8]

        return {
            'name': 'Expert Agent',
            'core_skills': ['analysis', 'research', 'communication'],
            'keywords': keywords if keywords else ['expert', 'knowledge', 'specialist'],
            'personality_traits': ['analytical', 'thorough'],
            'secondary_skills': ['collaboration', 'problem-solving'],
            'creation_cost': cost
        }

    def _generate_fallback_prompt(self, agent_details: Dict, expertise: str) -> str:
        """Generate fallback system prompt if API fails."""
        name = agent_details.get('name', 'Expert Agent')
        skills = ', '.join(agent_details.get('core_skills', ['analysis'])[:3])

        return f"""# {name}

You are {name}, an expert specializing in {expertise}.

## Expertise

Your core skills include {skills}. You bring deep knowledge and analytical thinking to discussions.

## Conversation Style

- Provide clear, well-reasoned insights
- Support arguments with evidence and examples
- Engage constructively with other agents
- Keep responses concise (2-4 sentences)
- Ask clarifying questions when needed

## Your Role

When collaborating with other AI agents, focus on contributing your unique expertise while remaining open to different perspectives. Your goal is to help reach well-informed conclusions through thoughtful dialogue.

Remember: You're having a conversation with other AI agents. Be genuine, professional, and collaborative."""

    def get_total_cost(self) -> float:
        """Get total cost of all agents created by this factory."""
        return self.total_creation_cost

    def get_agents_created_count(self) -> int:
        """Get number of agents created by this factory."""
        return self.agents_created
