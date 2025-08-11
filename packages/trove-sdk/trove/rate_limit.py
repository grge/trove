"""Rate limiting implementation for Trove SDK.

This module provides rate limiting using a token bucket algorithm to ensure
respectful API usage and prevent rate limit errors from the Trove API.
"""

import asyncio
import random
import threading
import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    """Token bucket for rate limiting.
    
    Implements a token bucket algorithm where tokens are added at a constant rate
    up to a maximum capacity. Requests consume tokens, and if no tokens are
    available, the request must wait.
    
    Args:
        rate: Rate at which tokens are added (tokens per second)
        capacity: Maximum number of tokens the bucket can hold
        tokens: Initial number of tokens in the bucket
        last_update: Timestamp of last token addition
        
    Example:
        >>> bucket = TokenBucket(rate=2.0, capacity=5, tokens=5, last_update=time.time())
        >>> # Try to consume a token
        >>> if bucket.consume(1):
        ...     print("Token consumed, request allowed")
        ... else:
        ...     wait_time = bucket.time_to_tokens(1)
        ...     print(f"Must wait {wait_time:.2f} seconds")
    """
    rate: float  # tokens per second
    capacity: int  # max tokens
    tokens: float
    last_update: float

    def __post_init__(self):
        """Ensure tokens don't exceed capacity."""
        self.tokens = min(self.tokens, self.capacity)

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket.
        
        This method first refills the bucket based on elapsed time,
        then attempts to consume the requested number of tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were successfully consumed, False otherwise
        """
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def time_to_tokens(self, tokens: int = 1) -> float:
        """Calculate time until requested tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time in seconds until tokens will be available
        """
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.rate


class RateLimiter:
    """Rate limiter using token bucket algorithm with concurrency control.
    
    Provides both synchronous and asynchronous rate limiting with support
    for maximum concurrent requests. Uses a token bucket to enforce rate
    limits and a semaphore to control concurrency.
    
    Args:
        rate: Maximum requests per second
        burst: Maximum burst capacity (number of tokens in bucket)
        max_concurrency: Maximum number of concurrent requests
        
    Example:
        >>> limiter = RateLimiter(rate=2.0, burst=5, max_concurrency=3)
        >>> 
        >>> # Synchronous usage
        >>> limiter.acquire()  # Blocks until permission is granted
        >>> try:
        ...     # Make API request
        ...     pass
        ... finally:
        ...     limiter.release()
        >>> 
        >>> # Async usage
        >>> async def make_request():
        ...     await limiter.aacquire()
        ...     try:
        ...         # Make API request
        ...         pass
        ...     finally:
        ...         limiter.arelease()
    """

    def __init__(self, rate: float, burst: int, max_concurrency: int):
        self.bucket = TokenBucket(
            rate=rate,
            capacity=burst,
            tokens=burst,
            last_update=time.time()
        )
        self.max_concurrency = max_concurrency
        self.active_requests = 0
        self._lock = threading.Lock()
        self._async_semaphore = asyncio.Semaphore(max_concurrency)

    def acquire(self, timeout: float | None = None) -> bool:
        """Acquire permission for a request (blocking).
        
        Blocks until both a token is available from the bucket and
        there's an available concurrency slot.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if permission was acquired, False if timeout occurred
            
        Example:
            >>> limiter = RateLimiter(rate=1.0, burst=2, max_concurrency=2)
            >>> if limiter.acquire(timeout=5.0):
            ...     try:
            ...         # Make request
            ...         pass
            ...     finally:
            ...         limiter.release()
            ... else:
            ...     print("Timeout waiting for rate limit")
        """
        start_time = time.time() if timeout is not None else None

        with self._lock:
            # Wait for available concurrency slot
            while self.active_requests >= self.max_concurrency:
                if timeout is not None and (time.time() - start_time) >= timeout:
                    return False
                time.sleep(0.01)  # Short sleep to prevent busy waiting

            # Wait for available token
            while not self.bucket.consume():
                if timeout is not None and (time.time() - start_time) >= timeout:
                    return False

                wait_time = self.bucket.time_to_tokens()
                # Add small random jitter to prevent thundering herd
                jitter = random.uniform(0, 0.01)
                time.sleep(min(wait_time + jitter, 0.1))

            self.active_requests += 1
            return True

    def release(self) -> None:
        """Release request slot.
        
        Should be called when the request is complete to free up
        a concurrency slot for other requests.
        """
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)

    async def aacquire(self, timeout: float | None = None) -> bool:
        """Async acquire permission for a request.
        
        Asynchronously waits until both a token is available from the bucket
        and there's an available concurrency slot.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if permission was acquired, False if timeout occurred
            
        Example:
            >>> limiter = RateLimiter(rate=1.0, burst=2, max_concurrency=2)
            >>> if await limiter.aacquire(timeout=5.0):
            ...     try:
            ...         # Make async request
            ...         pass
            ...     finally:
            ...         limiter.arelease()
        """
        try:
            # Use asyncio.wait_for for timeout support
            if timeout is not None:
                await asyncio.wait_for(self._aacquire_impl(), timeout=timeout)
            else:
                await self._aacquire_impl()
            return True
        except asyncio.TimeoutError:
            return False

    async def _aacquire_impl(self) -> None:
        """Internal async acquire implementation."""
        async with self._async_semaphore:
            # Wait for available token
            while True:
                with self._lock:
                    if self.bucket.consume():
                        break
                    wait_time = self.bucket.time_to_tokens()

                # Add small random jitter to prevent thundering herd
                jitter = random.uniform(0, 0.01)
                await asyncio.sleep(min(wait_time + jitter, 0.1))

    def arelease(self) -> None:
        """Release async request slot.
        
        Note: This is not actually async, but provided for API consistency.
        The semaphore is automatically released when exiting the async context.
        """
        # The semaphore handles release automatically when exiting the context
        # This method is provided for API consistency but is essentially a no-op
        pass

    def stats(self) -> dict:
        """Get current rate limiter statistics.
        
        Returns:
            Dictionary with current state information
            
        Example:
            >>> limiter = RateLimiter(rate=2.0, burst=5, max_concurrency=3)
            >>> stats = limiter.stats()
            >>> print(f"Available tokens: {stats['tokens']}")
            >>> print(f"Active requests: {stats['active_requests']}")
        """
        with self._lock:
            # Update tokens based on current time
            now = time.time()
            elapsed = now - self.bucket.last_update
            current_tokens = min(
                self.bucket.capacity,
                self.bucket.tokens + elapsed * self.bucket.rate
            )

            return {
                'rate': self.bucket.rate,
                'capacity': self.bucket.capacity,
                'tokens': current_tokens,
                'active_requests': self.active_requests,
                'max_concurrency': self.max_concurrency,
            }


class ExponentialBackoff:
    """Exponential backoff with jitter for retry logic.
    
    Implements exponential backoff with optional jitter to spread out
    retry attempts and avoid thundering herd problems.
    
    Args:
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Multiplier for exponential backoff
        jitter: Whether to add random jitter
        
    Example:
        >>> backoff = ExponentialBackoff(base_delay=1.0, max_delay=60.0)
        >>> for attempt in range(3):
        ...     delay = backoff.calculate_delay(attempt)
        ...     print(f"Attempt {attempt}: wait {delay:.2f} seconds")
        ...     time.sleep(delay)
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.
        
        Args:
            attempt: Attempt number (0-based)
            
        Returns:
            Delay in seconds for this attempt
        """
        # Calculate exponential delay
        delay = self.base_delay * (self.multiplier ** attempt)
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter and delay > 0:
            # Add up to 25% random jitter
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)  # Ensure non-negative

        return delay

    async def async_sleep(self, attempt: int) -> None:
        """Async sleep for calculated delay.
        
        Args:
            attempt: Attempt number (0-based)
        """
        delay = self.calculate_delay(attempt)
        await asyncio.sleep(delay)

    def sleep(self, attempt: int) -> None:
        """Synchronous sleep for calculated delay.
        
        Args:
            attempt: Attempt number (0-based)
        """
        delay = self.calculate_delay(attempt)
        time.sleep(delay)
