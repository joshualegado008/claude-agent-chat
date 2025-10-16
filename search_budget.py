"""
Search Budget Manager - Prevents API abuse and cost overruns
Implements hard limits at multiple levels with circuit breaker pattern
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple
import threading


@dataclass
class BudgetLimits:
    """Configuration for search budget limits"""
    max_searches_per_turn: int = 3
    max_searches_per_conversation: int = 15
    max_requests_per_minute: int = 10
    cooldown_turns: int = 1


class SearchBudget:
    """
    Enforces search limits to prevent cost overruns.

    Implements:
    - Per-turn limits (prevent spam in single turn)
    - Per-conversation limits (total cap for session)
    - Per-minute rate limiting (sliding window)
    - Cooldown periods (wait N turns between searches)
    - Circuit breaker (auto-disable on repeated failures)
    """

    def __init__(self, limits: BudgetLimits):
        self.limits = limits
        self.conversation_count = 0
        self.current_turn_count = 0
        self.last_search_turn = -999
        self.current_turn = 0

        # Rate limiting with sliding window
        self.request_times = []
        self.lock = threading.Lock()

        # Circuit breaker state
        self.failures = 0
        self.circuit_open = False
        self.circuit_open_until = None

    def can_search(self, turn_number: int) -> Tuple[bool, str]:
        """
        Check if search is allowed.

        Args:
            turn_number: Current conversation turn

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        with self.lock:
            # Update turn if changed
            if turn_number != self.current_turn:
                self.current_turn = turn_number
                self.current_turn_count = 0

            # Check circuit breaker
            if self.circuit_open:
                if datetime.now() < self.circuit_open_until:
                    return False, "Circuit breaker open (too many failures, retry in 5min)"
                else:
                    # Reset circuit breaker
                    self.circuit_open = False
                    self.failures = 0

            # Check per-conversation limit
            if self.conversation_count >= self.limits.max_searches_per_conversation:
                return False, f"Conversation limit reached ({self.limits.max_searches_per_conversation} searches)"

            # Check turn cooldown
            turns_since_last = turn_number - self.last_search_turn
            if turns_since_last < self.limits.cooldown_turns:
                remaining = self.limits.cooldown_turns - turns_since_last
                return False, f"Cooldown active (wait {remaining} more turn(s))"

            # Check per-turn limit
            if self.current_turn_count >= self.limits.max_searches_per_turn:
                return False, f"Turn limit reached ({self.limits.max_searches_per_turn} searches per turn)"

            # Check rate limiting (sliding window)
            now = datetime.now()
            cutoff = now - timedelta(minutes=1)
            self.request_times = [t for t in self.request_times if t > cutoff]

            if len(self.request_times) >= self.limits.max_requests_per_minute:
                return False, f"Rate limit exceeded ({self.limits.max_requests_per_minute} requests/minute)"

            return True, "OK"

    def record_search(self, turn_number: int, success: bool = True):
        """
        Record a search attempt.

        Args:
            turn_number: Current turn
            success: Whether search succeeded
        """
        with self.lock:
            self.request_times.append(datetime.now())
            self.conversation_count += 1
            self.current_turn_count += 1
            self.last_search_turn = turn_number

            # Update circuit breaker state
            if not success:
                self.failures += 1
                if self.failures >= 3:
                    # Open circuit breaker for 5 minutes
                    self.circuit_open = True
                    self.circuit_open_until = datetime.now() + timedelta(minutes=5)
                    print(f"⚠️  Circuit breaker opened (3 consecutive failures)")
            else:
                # Successful search reduces failure count
                self.failures = max(0, self.failures - 1)

    def get_stats(self) -> dict:
        """Return current budget statistics"""
        with self.lock:
            return {
                'conversation_searches': self.conversation_count,
                'turn_searches': self.current_turn_count,
                'remaining_conversation': self.limits.max_searches_per_conversation - self.conversation_count,
                'circuit_breaker_open': self.circuit_open,
                'failure_count': self.failures,
                'requests_last_minute': len(self.request_times)
            }

    def reset_conversation(self):
        """Reset counters for new conversation"""
        with self.lock:
            self.conversation_count = 0
            self.current_turn_count = 0
            self.last_search_turn = -999
            self.current_turn = 0
            self.request_times = []
            self.failures = 0
            self.circuit_open = False
            self.circuit_open_until = None
