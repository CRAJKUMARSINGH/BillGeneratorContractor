#!/usr/bin/env python3
"""
API Key Manager - Week 4 Day 2
Manages multiple API keys with rotation and quota tracking
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum


class KeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    QUOTA_EXCEEDED = "quota_exceeded"
    INVALID = "invalid"
    DISABLED = "disabled"


@dataclass
class APIKey:
    """API key with metadata"""
    key: str
    name: str
    status: KeyStatus = KeyStatus.ACTIVE
    requests_made: int = 0
    daily_quota: Optional[int] = None
    last_used: Optional[datetime] = None
    last_error: Optional[str] = None
    quota_reset_time: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if key is available for use"""
        if self.status != KeyStatus.ACTIVE:
            return False
        
        # Check if quota has reset
        if self.quota_reset_time and datetime.now() >= self.quota_reset_time:
            self.status = KeyStatus.ACTIVE
            self.requests_made = 0
            self.quota_reset_time = None
        
        # Check quota
        if self.daily_quota and self.requests_made >= self.daily_quota:
            return False
        
        return True
    
    def mark_used(self):
        """Mark key as used"""
        self.requests_made += 1
        self.last_used = datetime.now()
    
    def mark_quota_exceeded(self, reset_hours: int = 24):
        """Mark key as quota exceeded"""
        self.status = KeyStatus.QUOTA_EXCEEDED
        self.quota_reset_time = datetime.now() + timedelta(hours=reset_hours)
        self.last_error = "Quota exceeded"
    
    def mark_invalid(self, error: str):
        """Mark key as invalid"""
        self.status = KeyStatus.INVALID
        self.last_error = error


class APIKeyManager:
    """Manages multiple API keys with automatic rotation"""
    
    def __init__(self, keys: List[APIKey]):
        self.keys = keys
        self.current_index = 0
    
    def get_current_key(self) -> Optional[APIKey]:
        """Get current active key"""
        # Try current key first
        if self.keys[self.current_index].is_available():
            return self.keys[self.current_index]
        
        # Try to find next available key
        for i in range(len(self.keys)):
            index = (self.current_index + i) % len(self.keys)
            if self.keys[index].is_available():
                self.current_index = index
                return self.keys[index]
        
        return None
    
    def rotate_key(self) -> Optional[APIKey]:
        """Rotate to next available key"""
        for i in range(1, len(self.keys) + 1):
            index = (self.current_index + i) % len(self.keys)
            if self.keys[index].is_available():
                self.current_index = index
                print(f"  Rotated to key: {self.keys[index].name}")
                return self.keys[index]
        
        print(f"  No available keys!")
        return None
    
    def mark_current_used(self):
        """Mark current key as used"""
        if 0 <= self.current_index < len(self.keys):
            self.keys[self.current_index].mark_used()
    
    def mark_current_quota_exceeded(self):
        """Mark current key as quota exceeded and rotate"""
        if 0 <= self.current_index < len(self.keys):
            key = self.keys[self.current_index]
            key.mark_quota_exceeded()
            print(f"  Key '{key.name}' quota exceeded")
            return self.rotate_key()
        return None
    
    def mark_current_invalid(self, error: str):
        """Mark current key as invalid and rotate"""
        if 0 <= self.current_index < len(self.keys):
            key = self.keys[self.current_index]
            key.mark_invalid(error)
            print(f"  Key '{key.name}' marked invalid: {error}")
            return self.rotate_key()
        return None
    
    def get_status(self) -> dict:
        """Get status of all keys"""
        return {
            'total_keys': len(self.keys),
            'active_keys': sum(1 for k in self.keys if k.status == KeyStatus.ACTIVE),
            'quota_exceeded': sum(1 for k in self.keys if k.status == KeyStatus.QUOTA_EXCEEDED),
            'invalid_keys': sum(1 for k in self.keys if k.status == KeyStatus.INVALID),
            'current_key': self.keys[self.current_index].name if self.keys else None,
            'keys': [
                {
                    'name': k.name,
                    'status': k.status.value,
                    'requests': k.requests_made,
                    'quota': k.daily_quota,
                    'last_used': k.last_used.isoformat() if k.last_used else None,
                    'available': k.is_available()
                }
                for k in self.keys
            ]
        }


if __name__ == '__main__':
    # Test the API key manager
    print("\n" + "="*80)
    print("API KEY MANAGER TEST - WEEK 4 DAY 2")
    print("="*80)
    
    # Create test keys
    keys = [
        APIKey(
            key="key1_test",
            name="Primary Key",
            daily_quota=20
        ),
        APIKey(
            key="key2_test",
            name="Backup Key 1",
            daily_quota=20
        ),
        APIKey(
            key="key3_test",
            name="Backup Key 2",
            daily_quota=20
        )
    ]
    
    manager = APIKeyManager(keys)
    
    # Test 1: Get current key
    print("\nTest 1: Get current key")
    print("-" * 80)
    
    current = manager.get_current_key()
    print(f"Current key: {current.name}")
    print(f"Available: {current.is_available()}")
    
    # Test 2: Simulate usage
    print("\n" + "="*80)
    print("Test 2: Simulate API usage")
    print("-" * 80)
    
    for i in range(25):
        key = manager.get_current_key()
        if key:
            manager.mark_current_used()
            print(f"Request {i+1}: Using {key.name} (requests: {key.requests_made}/{key.daily_quota})")
            
            # Simulate quota exceeded
            if key.requests_made >= key.daily_quota:
                print(f"  Quota exceeded for {key.name}")
                manager.mark_current_quota_exceeded()
        else:
            print(f"Request {i+1}: No available keys!")
            break
    
    # Test 3: Show status
    print("\n" + "="*80)
    print("Test 3: Key status")
    print("-" * 80)
    
    status = manager.get_status()
    print(f"\nTotal keys: {status['total_keys']}")
    print(f"Active keys: {status['active_keys']}")
    print(f"Quota exceeded: {status['quota_exceeded']}")
    print(f"Current key: {status['current_key']}")
    
    print(f"\nKey details:")
    for key_info in status['keys']:
        print(f"  {key_info['name']}:")
        print(f"    Status: {key_info['status']}")
        print(f"    Requests: {key_info['requests']}/{key_info['quota']}")
        print(f"    Available: {key_info['available']}")
    
    # Test 4: Invalid key handling
    print("\n" + "="*80)
    print("Test 4: Invalid key handling")
    print("-" * 80)
    
    # Reset keys
    for key in keys:
        key.status = KeyStatus.ACTIVE
        key.requests_made = 0
    
    manager.current_index = 0
    
    # Mark first key as invalid
    manager.mark_current_invalid("Authentication failed")
    
    # Try to get key
    current = manager.get_current_key()
    if current:
        print(f"Rotated to: {current.name}")
    
    print("\n" + "="*80)
    print("API KEY MANAGER: OPERATIONAL")
    print("="*80 + "\n")
