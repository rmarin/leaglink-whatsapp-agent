#!/bin/bash

# test.sh - Comprehensive testing script for Legalink WhatsApp Agent
# Usage: ./test.sh [OPTIONS]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COVERAGE=false
VERBOSE=false
QUIET=false
HTML_REPORT=false
JUNIT_XML=false
TEST_CATEGORY=""
SPECIFIC_FILE=""
PARALLEL=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Legalink WhatsApp Agent Test Runner

USAGE:
    ./test.sh [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -c, --coverage          Run tests with coverage report
    -v, --verbose           Run tests in verbose mode
    -q, --quiet             Run tests in quiet mode
    -H, --html              Generate HTML coverage report
    -x, --xml               Generate JUnit XML report
    -p, --parallel          Run tests in parallel
    
    # Test Categories
    --unit                  Run only unit tests
    --integration          Run only integration tests
    --api                  Run only API tests
    --webhook              Run only webhook tests
    --agent                Run only agent tests
    --simple               Run only simple tests
    --comprehensive        Run only comprehensive tests
    --connections          Run only connection tests
    
    # Specific Files
    -f, --file FILE        Run specific test file
    
    # Examples
    ./test.sh                           # Run all tests
    ./test.sh --unit --coverage         # Run unit tests with coverage
    ./test.sh --verbose --html          # Run all tests verbose with HTML report
    ./test.sh -f test_simple.py         # Run specific test file
    ./test.sh --api --xml              # Run API tests with XML output

EOF
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed"
        exit 1
    fi
    
    # Check pytest
    if ! python3 -c "import pytest" &> /dev/null; then
        print_error "pytest is not installed. Run: pip install pytest"
        exit 1
    fi
    
    # Check if in virtual environment (recommended)
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Not running in a virtual environment"
    fi
    
    print_success "Dependencies check passed"
}

# Function to validate environment
check_environment() {
    print_status "Checking test environment..."
    
    # Required test environment variables are set by conftest.py fixtures
    # But we can check if the test configuration files exist
    
    if [[ ! -f "pytest.ini" ]]; then
        print_error "pytest.ini not found"
        exit 1
    fi
    
    if [[ ! -d "tests" ]]; then
        print_error "tests directory not found"
        exit 1
    fi
    
    if [[ ! -f "tests/conftest.py" ]]; then
        print_error "tests/conftest.py not found"
        exit 1
    fi
    
    print_success "Environment check passed"
}

# Function to build pytest command
build_pytest_command() {
    local cmd="python3 -m pytest"
    
    # Add coverage if requested
    if [[ "$COVERAGE" == true ]]; then
        cmd="$cmd --cov=app --cov-report=term-missing"
        
        if [[ "$HTML_REPORT" == true ]]; then
            cmd="$cmd --cov-report=html:htmlcov"
        fi
    fi
    
    # Add verbosity
    if [[ "$VERBOSE" == true ]]; then
        cmd="$cmd -v"
    elif [[ "$QUIET" == true ]]; then
        cmd="$cmd -q"
    fi
    
    # Add JUnit XML output
    if [[ "$JUNIT_XML" == true ]]; then
        cmd="$cmd --junitxml=test-results.xml"
    fi
    
    # Add parallel execution
    if [[ "$PARALLEL" == true ]]; then
        # Check if pytest-xdist is available
        if python3 -c "import xdist" &> /dev/null; then
            cmd="$cmd -n auto"
        else
            print_warning "pytest-xdist not available, running tests sequentially"
        fi
    fi
    
    # Add test category markers
    if [[ -n "$TEST_CATEGORY" ]]; then
        cmd="$cmd -m $TEST_CATEGORY"
    fi
    
    # Add specific file
    if [[ -n "$SPECIFIC_FILE" ]]; then
        if [[ -f "tests/$SPECIFIC_FILE" ]]; then
            cmd="$cmd tests/$SPECIFIC_FILE"
        else
            print_error "Test file not found: tests/$SPECIFIC_FILE"
            exit 1
        fi
    else
        cmd="$cmd tests/"
    fi
    
    echo "$cmd"
}

# Function to run tests
run_tests() {
    local pytest_cmd=$(build_pytest_command)
    
    print_status "Running tests..."
    print_status "Command: $pytest_cmd"
    echo
    
    # Execute the command
    if eval "$pytest_cmd"; then
        print_success "All tests passed!"
        
        # Show coverage report location if generated
        if [[ "$COVERAGE" == true && "$HTML_REPORT" == true ]]; then
            print_status "HTML coverage report generated at: htmlcov/index.html"
        fi
        
        # Show JUnit XML location if generated
        if [[ "$JUNIT_XML" == true ]]; then
            print_status "JUnit XML report generated at: test-results.xml"
        fi
        
        return 0
    else
        print_error "Some tests failed!"
        return 1
    fi
}

# Function to clean previous reports
clean_reports() {
    print_status "Cleaning previous reports..."
    
    if [[ -d "htmlcov" ]]; then
        rm -rf htmlcov
    fi
    
    if [[ -f "test-results.xml" ]]; then
        rm -f test-results.xml
    fi
    
    if [[ -f ".coverage" ]]; then
        rm -f .coverage
    fi
    
    # Clean pytest cache
    if [[ -d ".pytest_cache" ]]; then
        rm -rf .pytest_cache
    fi
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -H|--html)
            HTML_REPORT=true
            COVERAGE=true  # HTML report requires coverage
            shift
            ;;
        -x|--xml)
            JUNIT_XML=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        --unit)
            TEST_CATEGORY="unit"
            shift
            ;;
        --integration)
            TEST_CATEGORY="integration"
            shift
            ;;
        --api)
            TEST_CATEGORY="api"
            shift
            ;;
        --webhook)
            TEST_CATEGORY="webhook"
            shift
            ;;
        --agent)
            TEST_CATEGORY="agent"
            shift
            ;;
        --simple)
            SPECIFIC_FILE="test_simple.py"
            shift
            ;;
        --comprehensive)
            SPECIFIC_FILE="test_comprehensive.py"
            shift
            ;;
        --connections)
            SPECIFIC_FILE="test_connections.py"
            shift
            ;;
        -f|--file)
            if [[ -n "$2" ]]; then
                SPECIFIC_FILE="$2"
                shift 2
            else
                print_error "Option --file requires a filename"
                exit 1
            fi
            ;;
        --clean)
            clean_reports
            print_success "Reports cleaned"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Legalink WhatsApp Agent Test Runner"
    echo "======================================="
    echo
    
    # Clean previous reports
    clean_reports
    
    # Check dependencies and environment
    check_dependencies
    check_environment
    
    echo
    
    # Run tests
    if run_tests; then
        echo
        print_success "Testing completed successfully!"
        exit 0
    else
        echo
        print_error "Testing failed!"
        exit 1
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi