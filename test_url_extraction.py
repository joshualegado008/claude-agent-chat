#!/usr/bin/env python3
"""
Test URL extraction from metadata_extractor
"""

import re

# Test the regex pattern (same as in metadata_extractor.py)
url_pattern = r'https?://[^\s<>"\'})\]]+'

# User's title
title = """recently we have seen research on jailbreaking LLM's and context poisoniong, reference: https://icml.cc/virtual/2025/poster/45356 and https://www.anthropic.com/research/small-samples-poison. debate the issue and how we can prevent and mitigate this going forward, using established cyber security principles for software."""

print("Testing URL Extraction")
print("="*60)
print(f"Title: {title}")
print()

# Extract URLs
urls = re.findall(url_pattern, title)

print(f"URLs found (raw): {len(urls)}")
for i, url in enumerate(urls, 1):
    print(f"  {i}. {url}")
print()

# Check if period is included
has_punctuation = False
if urls:
    for url in urls:
        if url.endswith('.'):
            print(f"⚠️  URL ends with period: {url}")
            has_punctuation = True

if has_punctuation:
    print("\n" + "="*60)
    print("Testing punctuation cleanup:")
    print("="*60)
    cleaned_urls = []
    for url in urls:
        cleaned = url.rstrip('.,;:!?')
        cleaned_urls.append(cleaned)
        if url != cleaned:
            print(f"  Cleaned: {url} → {cleaned}")

    print(f"\nFinal cleaned URLs: {len(cleaned_urls)}")
    for i, url in enumerate(cleaned_urls, 1):
        print(f"  {i}. {url}")
