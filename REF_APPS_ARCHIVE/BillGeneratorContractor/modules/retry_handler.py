#!/usr/bin/env python3
"""
Retry Handler - Week 4 Day 1
Exponential backoff retry with configurable policies
"""
import time
import functools
from typing import Callable, Optional, Tuple, Type
from dataclasses import dataclass
from enum import Enum


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        else:  # FIXED
            delay = self.initial_delay
        
        return min(delay, self.max_delay)


@dataclass
class RetryResult:
    """Result of retry operation"""
    success: bool
    result: any
    attempts: int
    total_time: float
    errors: list


class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
    
    def execute(
        self,
        func: Callable,
        *args,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> RetryResult:
        """Execute function with retry logic"""
        start_time = time.time()
        errors = []
        
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                total_time = time.time() - start_time
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt,
                    total_time=total_time,
                    errors=errors
                )
            
            except retryable_exceptions as e:
                errors.append({
                    'attempt': attempt,
                    'error': str(e),
                    'type': type(e).__name__
                })
                
                if attempt < self.policy.max_attempts:
                    delay = self.policy.calculate_delay(attempt)
                    print(f"  Attempt {attempt} failed: {e}")
                    print(f"  Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"  All {self.policy.max_attempts} attempts failed")
        
        total_time = time.time() - start_time
        return RetryResult(
            success=False,
            result=None,
            attempts=self.policy.max_attempts,
            total_time=total_time,
            errors=errors
        )


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for automatic retry with exponential backoff"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            policy = RetryPolicy(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                strategy=strategy
            )
            
            handler = RetryHandler(policy)
            result = handler.execute(
                func,
                *args,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
            
            if result.success:
                return result.result
            else:
                # Raise the last error
                last_error = result.errors[-1]
                raise Exception(f"Failed after {result.attempts} attempts: {last_error['error']}")
        
        return wrapper
    return decorator


# Common retry policies
QUICK_RETRY = RetryPolicy(
    max_attempts=2,
    initial_delay=0.5,
    max_delay=2.0,
    exponential_base=2.0
)

STANDARD_RETRY = RetryPolicy(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0
)

AGGRESSIVE_RETRY = RetryPolicy(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0
)


if __name__ == '__main__':
    # Test the retry handler
    print("\n" + "="*80)
    print("RETRY HANDLER TEST - WEEK 4 DAY 1")
    print("="*80)
    
    # Test 1: Function that succeeds on 3rd attempt
    print("\nTest 1: Function succeeds on 3rd attempt")
    print("-" * 80)
    
    attempt_counter = {'count': 0}
    
    def flaky_function():
        attempt_counter['count'] += 1
        if attempt_counter['count'] < 3:
            raise Exception(f"Simulated failure (attempt {attempt_counter['count']})")
        return "Success!"
    
    handler = RetryHandler(STANDARD_RETRY)
    result = handler.execute(flaky_function)
    
    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Result: {result.result}")
    print(f"  Attempts: {result.attempts}")
    print(f"  Total time: {result.total_time:.2f}s")
    print(f"  Errors: {len(result.errors)}")
    
    # Test 2: Function that always fails
    print("\n" + "="*80)
    print("Test 2: Function always fails")
    print("-" * 80)
    
    def always_fails():
        raise Exception("This always fails")
    
    handler = RetryHandler(QUICK_RETRY)
    result = handler.execute(always_fails)
    
    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Attempts: {result.attempts}")
    print(f"  Total time: {result.total_time:.2f}s")
    print(f"  Errors: {len(result.errors)}")
    
    # Test 3: Using decorator
    print("\n" + "="*80)
    print("Test 3: Using retry decorator")
    print("-" * 80)
    
    call_count = {'count': 0}
    
    @retry(max_attempts=3, initial_delay=0.5, exponential_base=2.0)
    def decorated_function():
        call_count['count'] += 1
        if call_count['count'] < 2:
            raise Exception(f"Decorated failure (attempt {call_count['count']})")
        return "Decorated success!"
    
    try:
        result = decorated_function()
        print(f"\nResult: {result}")
        print(f"Total calls: {call_count['count']}")
    except Exception as e:
        print(f"\nFailed: {e}")
    
    # Test 4: Different retry strategies
    print("\n" + "="*80)
    print("Test 4: Retry strategies comparison")
    print("-" * 80)
    
    strategies = [
        (RetryStrategy.EXPONENTIAL, "Exponential (1s, 2s, 4s)"),
        (RetryStrategy.LINEAR, "Linear (1s, 2s, 3s)"),
        (RetryStrategy.FIXED, "Fixed (1s, 1s, 1s)")
    ]
    
    for strategy, description in strategies:
        policy = RetryPolicy(
            max_attempts=3,
            initial_delay=1.0,
            strategy=strategy
        )
        
        print(f"\n{description}:")
        for attempt in range(1, 4):
            delay = policy.calculate_delay(attempt)
            print(f"  Attempt {attempt}: {delay:.1f}s delay")
    
    print("\n" + "="*80)
    print("RETRY HANDLER: OPERATIONAL")
    print("="*80 + "\n")
