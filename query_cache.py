"""
Query Cache - Deduplicates identical searches within conversation
Uses normalized query hashing for fast lookups
"""

import hashlib
import pickle
import os
import threading
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, Tuple


class QueryCache:
    """
    Fast query deduplication using hashed normalized queries.
    Prevents searching for the same thing multiple times in one session.

    Features:
    - Normalizes queries (lowercase, whitespace, punctuation)
    - Hash-based fast lookup
    - Memory + disk caching
    - TTL-based expiration
    - Thread-safe for multi-threaded/async environments
    """

    def __init__(self, ttl_minutes: int = 15, cache_dir: str = ".cache/search", enabled: bool = True):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.memory_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.lock = threading.Lock()  # Thread safety

        # Create cache directory
        if self.enabled:
            os.makedirs(cache_dir, exist_ok=True)

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for comparison.
        Removes case, punctuation, extra whitespace.
        """
        # Lowercase and strip
        normalized = query.lower().strip()

        # Keep only alphanumeric and spaces
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())

        # Collapse multiple spaces
        normalized = ' '.join(normalized.split())

        return normalized

    def _hash_query(self, query: str) -> str:
        """Generate fast hash of normalized query"""
        normalized = self._normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def get(self, query: str) -> Optional[Any]:
        """
        Get cached result if available and fresh.

        Args:
            query: Search query

        Returns:
            Cached result or None if not found/expired
        """
        if not self.enabled:
            return None

        query_hash = self._hash_query(query)

        # Check memory cache first (fastest)
        with self.lock:
            if query_hash in self.memory_cache:
                result, timestamp = self.memory_cache[query_hash]
                if datetime.now() - timestamp < self.ttl:
                    return result
                else:
                    # Expired, remove from memory
                    del self.memory_cache[query_hash]

        # Check disk cache (outside lock - I/O heavy)
        cache_file = os.path.join(self.cache_dir, f"query_{query_hash}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    timestamp = cached_data['timestamp']

                    if datetime.now() - timestamp < self.ttl:
                        result = cached_data['result']
                        # Promote to memory cache
                        with self.lock:
                            self.memory_cache[query_hash] = (result, timestamp)
                        return result
                    else:
                        # Expired, remove file
                        os.remove(cache_file)
            except Exception as e:
                print(f"⚠️  Cache read error: {e}")
                # Remove corrupted cache file
                try:
                    os.remove(cache_file)
                except:
                    pass

        return None

    def set(self, query: str, result: Any):
        """
        Cache a search result.

        Args:
            query: Search query
            result: Result to cache
        """
        if not self.enabled:
            return

        query_hash = self._hash_query(query)
        timestamp = datetime.now()

        # Store in memory
        with self.lock:
            self.memory_cache[query_hash] = (result, timestamp)

        # Store on disk for persistence (outside lock - I/O heavy)
        cache_file = os.path.join(self.cache_dir, f"query_{query_hash}.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'result': result,
                    'timestamp': timestamp,
                    'original_query': query,
                    'normalized_query': self._normalize_query(query)
                }, f)
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")

    def clear_expired(self):
        """Remove expired cache entries from memory and disk"""
        now = datetime.now()

        # Clear expired from memory
        with self.lock:
            expired_keys = [
                k for k, (_, ts) in self.memory_cache.items()
                if now - ts >= self.ttl
            ]
            for key in expired_keys:
                del self.memory_cache[key]

        # Clear expired from disk (outside lock - I/O heavy)
        if not os.path.exists(self.cache_dir):
            return

        for filename in os.listdir(self.cache_dir):
            if not filename.startswith('query_'):
                continue

            filepath = os.path.join(self.cache_dir, filename)
            try:
                with open(filepath, 'rb') as f:
                    cached_data = pickle.load(f)
                    if now - cached_data['timestamp'] >= self.ttl:
                        os.remove(filepath)
            except Exception:
                # Remove corrupted files
                try:
                    os.remove(filepath)
                except:
                    pass

    def get_stats(self) -> dict:
        """Return cache statistics"""
        disk_entries = 0
        if os.path.exists(self.cache_dir):
            disk_entries = len([
                f for f in os.listdir(self.cache_dir)
                if f.startswith('query_')
            ])

        with self.lock:
            memory_entries = len(self.memory_cache)

        return {
            'memory_entries': memory_entries,
            'disk_entries': disk_entries,
            'ttl_minutes': self.ttl.total_seconds() / 60,
            'enabled': self.enabled
        }

    def clear_all(self):
        """Clear all cached data"""
        with self.lock:
            self.memory_cache.clear()

        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.startswith('query_'):
                    try:
                        os.remove(os.path.join(self.cache_dir, filename))
                    except:
                        pass
