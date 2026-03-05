#!/bin/bash

# Integration Test Runner for v3.0 ChordScout
# This script runs all integration tests and generates a report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "ChordScout v3.0 Integration Test Suite"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Check if required dependencies are installed
echo "Checking dependencies..."
python3 -c "import numpy, librosa, basic_pitch" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Some dependencies may be missing${NC}"
    echo "Install with: pip install -r requirements-test.txt"
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create test results directory
mkdir -p test_results

# Run tests
echo ""
echo "Running integration tests..."
echo ""

# Test 1: Bass-Only Mode (v2.0 Compatibility)
echo -e "${YELLOW}[1/7] Testing Bass-Only Mode...${NC}"
pytest test_integration_bass_only.py -v --tb=short 2>&1 | tee test_results/bass_only.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Bass-Only Mode tests passed${NC}"
else
    echo -e "${RED}✗ Bass-Only Mode tests failed${NC}"
fi
echo ""

# Test 2: Mode Selection Workflow
echo -e "${YELLOW}[2/7] Testing Mode Selection Workflow...${NC}"
pytest test_integration_mode_selection.py -v --tb=short 2>&1 | tee test_results/mode_selection.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Mode Selection tests passed${NC}"
else
    echo -e "${RED}✗ Mode Selection tests failed${NC}"
fi
echo ""

# Test 3: Key Confirmation Workflow
echo -e "${YELLOW}[3/7] Testing Key Confirmation Workflow...${NC}"
pytest test_integration_key_confirmation.py -v --tb=short 2>&1 | tee test_results/key_confirmation.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Key Confirmation tests passed${NC}"
else
    echo -e "${RED}✗ Key Confirmation tests failed${NC}"
fi
echo ""

# Test 4: Lyrics Integration
echo -e "${YELLOW}[4/7] Testing Lyrics Integration...${NC}"
pytest test_integration_lyrics.py -v --tb=short 2>&1 | tee test_results/lyrics.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Lyrics Integration tests passed${NC}"
else
    echo -e "${RED}✗ Lyrics Integration tests failed${NC}"
fi
echo ""

# Test 5: Error Handling
echo -e "${YELLOW}[5/7] Testing Error Handling...${NC}"
pytest test_integration_error_handling.py -v --tb=short 2>&1 | tee test_results/error_handling.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Error Handling tests passed${NC}"
else
    echo -e "${RED}✗ Error Handling tests failed${NC}"
fi
echo ""

# Test 6: Data Integrity
echo -e "${YELLOW}[6/7] Testing Data Integrity...${NC}"
pytest test_integration_data_integrity.py -v --tb=short 2>&1 | tee test_results/data_integrity.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Data Integrity tests passed${NC}"
else
    echo -e "${RED}✗ Data Integrity tests failed${NC}"
fi
echo ""

# Test 7: Parser and Serializer
echo -e "${YELLOW}[7/7] Testing Parser and Serializer...${NC}"
pytest test_integration_parser_serializer.py -v --tb=short 2>&1 | tee test_results/parser_serializer.log
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Parser and Serializer tests passed${NC}"
else
    echo -e "${RED}✗ Parser and Serializer tests failed${NC}"
fi
echo ""

# Run all tests with coverage
echo "=========================================="
echo "Running all tests with coverage..."
echo "=========================================="
echo ""

pytest test_integration_*.py -v --cov=. --cov-report=html --cov-report=term 2>&1 | tee test_results/coverage.log

# Generate summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""

# Count passed/failed tests
TOTAL_TESTS=$(grep -h "passed\|failed" test_results/*.log | tail -1)
echo "Results: $TOTAL_TESTS"

# Check if all tests passed
if grep -q "failed" test_results/*.log; then
    echo -e "${RED}Some tests failed. Check test_results/ for details.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
fi

echo ""
echo "Test logs saved to: test_results/"
echo "Coverage report: htmlcov/index.html"
echo ""
