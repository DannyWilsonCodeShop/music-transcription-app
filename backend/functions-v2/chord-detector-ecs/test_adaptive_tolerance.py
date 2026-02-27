#!/usr/bin/env python3
"""
Test adaptive tolerance in find_word_at_timestamp function
"""

import sys
import os

# Mock log function
def log(message, level="INFO"):
    """Mock logging function"""
    print(f"[{level}] {message}")

# Standalone implementation for testing
def find_word_at_timestamp(words, timestamp, tolerance=0.1, max_tolerance=0.5):
    """
    Find the word being sung at a given timestamp with adaptive tolerance
    
    Args:
        words: List of word dicts with 'start' and 'end' times
        timestamp: Time in seconds to find word for
        tolerance: Initial time tolerance in seconds (default 0.1s)
        max_tolerance: Maximum tolerance to try (default 0.5s)
    
    Returns:
        Word index (int) or None if no word found
    """
    # Try with initial tolerance
    for i, word in enumerate(words):
        if word['start'] - tolerance <= timestamp <= word['end'] + tolerance:
            return i
    
    # Check if timestamp is just before a word (anticipation)
    for i, word in enumerate(words):
        if word['start'] - 0.2 <= timestamp < word['start']:
            return i
    
    # If no match found, try with progressively larger tolerances up to max_tolerance
    current_tolerance = tolerance
    while current_tolerance < max_tolerance:
        # Double the tolerance, but don't exceed max_tolerance
        current_tolerance = min(current_tolerance * 2, max_tolerance)
        log(f"  No word found at {timestamp:.2f}s with previous tolerance, trying {current_tolerance:.2f}s", "WARNING")
        
        # Try again with increased tolerance
        for i, word in enumerate(words):
            if word['start'] - current_tolerance <= timestamp <= word['end'] + current_tolerance:
                log(f"  Found word at index {i} ('{word.get('word', 'N/A')}') with adaptive tolerance {current_tolerance:.2f}s", "INFO")
                return i
    
    # Log misalignment if still no match after trying all tolerances
    log(f"  Timestamp mismatch: No word found at {timestamp:.2f}s even with max tolerance {max_tolerance:.2f}s", "WARNING")
    
    return None  # Instrumental section

def test_exact_match():
    """Test finding word with exact timestamp match"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 0.9, 'end': 1.2}
    ]
    
    # Exact match within word
    result = find_word_at_timestamp(words, 0.6)
    assert result == 0, f"Expected 0, got {result}"
    print("✓ Exact match test passed")

def test_initial_tolerance():
    """Test finding word within initial tolerance (0.1s)"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 0.9, 'end': 1.2}
    ]
    
    # Just outside word but within 0.1s tolerance
    result = find_word_at_timestamp(words, 0.85)
    assert result == 0, f"Expected 0, got {result}"
    print("✓ Initial tolerance test passed")

def test_adaptive_tolerance():
    """Test adaptive tolerance when initial tolerance fails"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 1.2, 'end': 1.5}  # Larger gap
    ]
    
    # Timestamp at 1.0s - outside initial 0.1s tolerance but within 0.2s
    result = find_word_at_timestamp(words, 1.0)
    assert result == 1, f"Expected 1 (adaptive tolerance), got {result}"
    print("✓ Adaptive tolerance test passed")

def test_anticipation():
    """Test anticipation (chord before word starts)"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 0.9, 'end': 1.2}
    ]
    
    # Timestamp just before word (anticipation)
    result = find_word_at_timestamp(words, 0.4)
    assert result == 0, f"Expected 0 (anticipation), got {result}"
    print("✓ Anticipation test passed")

def test_no_match():
    """Test when no word found even with max tolerance"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 2.5, 'end': 2.8}  # Larger gap (1.5s from 1.0s)
    ]
    
    # Timestamp in large gap - should return None (instrumental)
    result = find_word_at_timestamp(words, 1.5)
    assert result is None, f"Expected None (instrumental), got {result}"
    print("✓ No match test passed")

def test_max_tolerance_boundary():
    """Test that adaptive tolerance respects max_tolerance"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 1.8, 'end': 2.1}
    ]
    
    # Timestamp at 1.4s - within 0.4s of word at 1.8s (will need adaptive tolerance)
    result = find_word_at_timestamp(words, 1.4)
    assert result == 1, f"Expected 1 (max tolerance), got {result}"
    print("✓ Max tolerance boundary test passed")

def test_beyond_max_tolerance():
    """Test that timestamps beyond max tolerance return None"""
    words = [
        {'word': 'Hello', 'start': 0.5, 'end': 0.8},
        {'word': 'world', 'start': 3.0, 'end': 3.3}
    ]
    
    # Timestamp at 1.5s - more than 0.5s from any word
    result = find_word_at_timestamp(words, 1.5)
    assert result is None, f"Expected None (beyond max tolerance), got {result}"
    print("✓ Beyond max tolerance test passed")

if __name__ == '__main__':
    print("Testing adaptive tolerance in find_word_at_timestamp...")
    print()
    
    try:
        test_exact_match()
        test_initial_tolerance()
        test_adaptive_tolerance()
        test_anticipation()
        test_no_match()
        test_max_tolerance_boundary()
        test_beyond_max_tolerance()
        
        print()
        print("=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        
    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"✗ Test failed: {e}")
        print("=" * 50)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"✗ Unexpected error: {e}")
        print("=" * 50)
        sys.exit(1)
