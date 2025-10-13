"""
Web Tools - URL fetching capability for Claude agents

Implements the fetch_url tool using Anthropic's Tools API, allowing agents
to autonomously browse and read web content during conversations.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from urllib.parse import urlparse
import re


def get_web_tools_schema() -> List[Dict]:
    """
    Get the tool schema for web browsing capabilities.

    Returns:
        List of tool definitions in Anthropic Tools API format
    """
    return [
        {
            "name": "fetch_url",
            "description": (
                "Fetch and read the content from a webpage. Use this tool when you need "
                "current information from the internet, want to verify claims with sources, "
                "or need to read content from a URL mentioned in the conversation. "
                "The tool returns the main text content of the page."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to fetch (must start with http:// or https://)"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "Brief explanation of why you're fetching this URL (optional, for logging)"
                    }
                },
                "required": ["url"]
            }
        }
    ]


def validate_url(url: str, config: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate URL against security rules.

    Args:
        url: The URL to validate
        config: Web browsing configuration with allowed/blocked domains

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Must start with http:// or https://
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"

        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix for comparison
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check blocked domains
        blocked_domains = config.get('blocked_domains', [])
        for blocked in blocked_domains:
            blocked_clean = blocked.lower().replace('www.', '')
            if blocked_clean in domain or domain.endswith('.' + blocked_clean):
                return False, f"Domain {domain} is blocked"

        # Check allowed domains (if specified)
        allowed_domains = config.get('allowed_domains', [])
        if allowed_domains:
            allowed = False
            for allowed_domain in allowed_domains:
                allowed_clean = allowed_domain.lower().replace('www.', '')
                if allowed_clean in domain or domain.endswith('.' + allowed_clean):
                    allowed = True
                    break
            if not allowed:
                return False, f"Domain {domain} is not in allowed list"

        return True, None

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def clean_html_content(html: str, config: Dict) -> str:
    """
    Extract clean, readable text from HTML.

    Args:
        html: Raw HTML content
        config: Configuration with content extraction settings

    Returns:
        Cleaned text content
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, and other non-content tags
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()

        # Extract metadata if configured
        metadata = []
        if config.get('include_metadata', True):
            # Get title
            title_tag = soup.find('title')
            if title_tag:
                metadata.append(f"Title: {title_tag.get_text().strip()}")

            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metadata.append(f"Description: {meta_desc['content'].strip()}")

        # Get main content
        # Try to find main content areas first
        main_content = soup.find('main') or soup.find('article') or soup.find('body')

        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # Limit content length
        max_length = config.get('max_content_length', 100000)
        if len(text) > max_length:
            text = text[:max_length] + f"\n\n[Content truncated at {max_length} characters]"

        # Combine metadata and content
        if metadata:
            return '\n'.join(metadata) + '\n\n' + text
        return text

    except Exception as e:
        return f"Error parsing HTML: {str(e)}"


def execute_fetch_url(url: str, purpose: Optional[str], config: Dict) -> str:
    """
    Execute the fetch_url tool - fetch and parse a webpage.

    Args:
        url: The URL to fetch
        purpose: Optional purpose/reason for fetching (for logging)
        config: Web browsing configuration

    Returns:
        String result to return to the agent (either content or error message)
    """
    # Validate URL
    is_valid, error = validate_url(url, config)
    if not is_valid:
        return f"❌ Cannot fetch URL: {error}"

    try:
        # Log the fetch attempt
        if purpose:
            print(f"🌐 Fetching URL: {url}")
            print(f"   Purpose: {purpose}")
        else:
            print(f"🌐 Fetching URL: {url}")

        # Fetch the URL
        timeout = config.get('timeout', 15)
        user_agent = config.get('user_agent', 'ClaudeAgentChat/1.0 (Research Bot)')

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'text/plain' not in content_type:
            return f"❌ URL does not return HTML content (Content-Type: {content_type})"

        # Parse and clean content
        clean_content = clean_html_content(response.text, config)

        print(f"✅ Successfully fetched {len(clean_content)} characters from {url}")

        return f"=== Content from {url} ===\n\n{clean_content}\n\n=== End of content ==="

    except requests.exceptions.Timeout:
        return f"❌ Timeout while fetching {url} (exceeded {timeout} seconds)"
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP error while fetching {url}: {e.response.status_code} {e.response.reason}"
    except requests.exceptions.ConnectionError:
        return f"❌ Connection error: Could not connect to {url}"
    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching URL: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


def execute_tool(tool_name: str, tool_input: Dict, config: Dict) -> str:
    """
    Execute a web tool by name.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        config: Web browsing configuration

    Returns:
        Tool execution result as string
    """
    if tool_name == "fetch_url":
        url = tool_input.get('url', '')
        purpose = tool_input.get('purpose')
        return execute_fetch_url(url, purpose, config)
    else:
        return f"❌ Unknown tool: {tool_name}"


def get_web_config(full_config: Dict) -> Dict:
    """
    Extract and validate web browsing configuration.

    Args:
        full_config: Full configuration dictionary from config.yaml

    Returns:
        Web browsing configuration with defaults
    """
    web_config = full_config.get('web_browsing', {})

    # Apply defaults
    defaults = {
        'enabled': True,
        'timeout': 15,
        'max_content_length': 100000,
        'max_urls_per_turn': 3,
        'allowed_domains': [],
        'blocked_domains': [],
        'user_agent': 'ClaudeAgentChat/1.0 (Research Bot)',
        'include_metadata': True,
        'extract_links': False
    }

    # Merge with defaults
    for key, default_value in defaults.items():
        if key not in web_config:
            web_config[key] = default_value

    return web_config
