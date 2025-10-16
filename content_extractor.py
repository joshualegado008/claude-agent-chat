"""
Content Extractor - Clean HTML to Markdown with metadata preservation
Pipeline: HTML → Readability → html2text → Clean Markdown
"""

import asyncio
from dataclasses import dataclass
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup
from readability import Document
import html2text
from datetime import datetime
import re


@dataclass
class ExtractedContent:
    """Clean extracted content with full metadata"""
    text: str
    title: str
    url: str
    site: str
    published_date: Optional[str]
    author: Optional[str]
    excerpt: str  # First 200 chars
    word_count: int
    extraction_method: str


class ContentExtractor:
    """
    Extract clean markdown content from web pages.

    Pipeline:
    1. Fetch HTML with proper headers
    2. Extract metadata (Open Graph, meta tags)
    3. Clean content with Readability
    4. Convert to Markdown
    5. Post-process and clean

    Features:
    - Preserves publish dates
    - Extracts author info
    - Generates excerpts
    - Handles errors gracefully
    """

    def __init__(self, config: dict):
        self.config = config
        extraction_config = config.get('search', {}).get('extraction', {})
        timeout_seconds = extraction_config.get('timeout', 10)
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        # Configure html2text
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = True
        self.html2text.ignore_emphasis = False
        self.html2text.body_width = 0  # No wrapping
        self.html2text.single_line_break = False

        # User agents for rotation
        user_agent = extraction_config.get('user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.user_agents = [user_agent]

    async def extract(self, url: str) -> Optional[ExtractedContent]:
        """
        Extract content from URL.

        Args:
            url: URL to extract from

        Returns:
            ExtractedContent or None if extraction fails
        """
        try:
            # Fetch HTML
            html = await self._fetch_html(url)
            if not html:
                return None

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Extract metadata
            metadata = self._extract_metadata(soup, url)

            # Extract main content using Readability
            doc = Document(html)
            clean_html = doc.summary()
            title = doc.title() or metadata.get('title', 'Untitled')

            # Convert to markdown
            markdown = self.html2text.handle(clean_html)
            markdown = self._clean_markdown(markdown)

            # Generate excerpt
            excerpt = markdown[:200].strip()
            if len(markdown) > 200:
                excerpt += "..."

            # Count words
            word_count = len(markdown.split())

            return ExtractedContent(
                text=markdown,
                title=title,
                url=url,
                site=metadata.get('site', self._extract_domain(url)),
                published_date=metadata.get('published_date'),
                author=metadata.get('author'),
                excerpt=excerpt,
                word_count=word_count,
                extraction_method='readability'
            )

        except Exception as e:
            print(f"⚠️  Extraction failed for {url}: {e}")
            return None

    async def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML with proper headers and error handling.

        Args:
            url: URL to fetch

        Returns:
            HTML string or None if fetch fails
        """
        headers = {
            'User-Agent': self.user_agents[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"⚠️  HTTP {response.status} for {url}")
                        return None
        except asyncio.TimeoutError:
            print(f"⚠️  Timeout fetching {url}")
            return None
        except Exception as e:
            print(f"⚠️  Fetch error for {url}: {e}")
            return None

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """
        Extract Open Graph and meta tags.

        Args:
            soup: BeautifulSoup object
            url: Original URL

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            metadata['title'] = og_title.get('content')
        elif soup.title:
            metadata['title'] = soup.title.string

        # Site name
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            metadata['site'] = og_site.get('content')

        # Published date
        date_patterns = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publication_date'}),
            ('meta', {'name': 'date'}),
            ('meta', {'property': 'og:article:published_time'}),
            ('time', {'class': 'published'}),
            ('time', {'datetime': True}),
        ]

        for tag, attrs in date_patterns:
            element = soup.find(tag, attrs)
            if element:
                date_str = element.get('content') or element.get('datetime')
                if date_str:
                    normalized = self._normalize_date(date_str)
                    if normalized:
                        metadata['published_date'] = normalized
                        break

        # Author
        author_patterns = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('meta', {'name': 'article:author'}),
            ('span', {'class': 'author'}),
            ('a', {'rel': 'author'}),
        ]

        for tag, attrs in author_patterns:
            element = soup.find(tag, attrs)
            if element:
                author = element.get('content') or element.text
                if author:
                    metadata['author'] = author.strip()
                    break

        return metadata

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date to YYYY-MM-DD format.

        Args:
            date_str: Date string in various formats

        Returns:
            Normalized date string or None
        """
        if not date_str:
            return None

        # Common ISO formats
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]

        for fmt in formats:
            try:
                # Take first 25 chars to handle timezone
                dt = datetime.strptime(date_str[:25].strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # If parsing fails, return original if it looks like a date
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str[:10]

        return None

    def _extract_domain(self, url: str) -> str:
        """
        Extract clean domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain name
        """
        match = re.search(r'://([^/]+)', url)
        if match:
            domain = match.group(1)
            # Remove www. prefix
            domain = re.sub(r'^www\.', '', domain)
            return domain
        return url

    def _clean_markdown(self, markdown: str) -> str:
        """
        Clean up markdown output.

        Args:
            markdown: Raw markdown from html2text

        Returns:
            Cleaned markdown
        """
        # Remove excessive newlines (more than 2)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Remove common navigation patterns
        nav_patterns = [
            r'(?i)Share\s*\|\s*Tweet\s*\|\s*Email.*?\n',
            r'(?i)Sign up for.*?newsletter.*?\n',
            r'(?i)Subscribe to.*?\n',
            r'(?i)Follow us on.*?\n'
        ]
        for pattern in nav_patterns:
            markdown = re.sub(pattern, '', markdown)

        # Remove multiple consecutive horizontal rules
        markdown = re.sub(r'(\*\*\*+\n?){2,}', '***\n', markdown)

        # Trim whitespace
        markdown = markdown.strip()

        return markdown

    def extract_sync(self, url: str) -> Optional[ExtractedContent]:
        """Synchronous wrapper for terminal use"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.extract(url))
