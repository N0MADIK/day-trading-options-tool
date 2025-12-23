"""
Trade Tracker Testing Suite
============================
Runs all test suites and displays consolidated results.

Usage:
  python testing_suite.py

This will run:
  - test_trade_tracker.py (29 unit tests)
  - test_api_endpoints.py (26 API tests)
  - verify_scheduler.py (scheduler verification)
"""

import sys
import os
import unittest
import traceback
from io import StringIO
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestResultCollector(unittest.TestResult):
    """Custom test result collector that stores detailed results"""
    
    def __init__(self):
        super().__init__()
        self.results = []
        self.current_test = None
    
    def startTest(self, test):
        self.current_test = str(test)
        super().startTest(test)
    
    def addSuccess(self, test):
        self.results.append({
            'name': str(test),
            'status': 'PASS',
            'error': None
        })
        super().addSuccess(test)
    
    def addFailure(self, test, err):
        self.results.append({
            'name': str(test),
            'status': 'FAIL',
            'error': self._format_error(err)
        })
        super().addFailure(test, err)
    
    def addError(self, test, err):
        self.results.append({
            'name': str(test),
            'status': 'ERROR',
            'error': self._format_error(err)
        })
        super().addError(test, err)
    
    def addSkip(self, test, reason):
        self.results.append({
            'name': str(test),
            'status': 'SKIP',
            'error': reason
        })
        super().addSkip(test, reason)
    
    def _format_error(self, err):
        """Format exception tuple to string"""
        if err is None:
            return None
        exc_type, exc_value, exc_tb = err
        # Get just the error message, not full traceback
        return f"{exc_type.__name__}: {exc_value}"


def print_header(text, char='='):
    """Print a formatted header"""
    width = 70
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)


def print_result(name, status, error=None):
    """Print a single test result"""
    # Shorten long test names
    if len(name) > 50:
        name = name[:47] + "..."
    
    if status == 'PASS':
        status_str = '\033[92m[PASS]\033[0m'  # Green
    elif status == 'FAIL':
        status_str = '\033[91m[FAIL]\033[0m'  # Red
    elif status == 'ERROR':
        status_str = '\033[91m[ERROR]\033[0m'  # Red
    elif status == 'SKIP':
        status_str = '\033[93m[SKIP]\033[0m'  # Yellow
    else:
        status_str = f'[{status}]'
    
    print(f"  {status_str} {name}")
    if error and status in ('FAIL', 'ERROR'):
        # Indent error message
        error_lines = str(error).split('\n')
        for line in error_lines[:3]:  # Limit to 3 lines
            print(f"         {line}")


def run_test_module(module_name, test_classes):
    """Run tests from a module and return results"""
    print_header(f"Running: {module_name}")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        try:
            suite.addTests(loader.loadTestsFromTestCase(test_class))
        except Exception as e:
            print(f"Error loading {test_class}: {e}")
    
    # Suppress stdout during tests
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        result = TestResultCollector()
        suite.run(result)
    finally:
        sys.stdout = old_stdout
    
    # Print results
    for r in result.results:
        print_result(r['name'], r['status'], r['error'])
    
    return result.results


def run_all_tests():
    """Run all test suites and display consolidated results"""
    start_time = datetime.now()
    all_results = []
    
    print_header("TRADE TRACKER TESTING SUITE", '=')
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ===== test_trade_tracker.py =====
    try:
        import test_trade_tracker
        
        test_classes = [
            test_trade_tracker.TestCompilation,
            test_trade_tracker.TestDatabaseSetup,
            test_trade_tracker.TestStrategiesService,
            test_trade_tracker.TestTradesService,
            test_trade_tracker.TestNotificationsService,
            test_trade_tracker.TestSchedulerModule,
        ]
        
        results = run_test_module("test_trade_tracker.py", test_classes)
        all_results.extend(results)
        
    except Exception as e:
        print(f"  [ERROR] Failed to load test_trade_tracker.py: {e}")
        all_results.append({
            'name': 'test_trade_tracker.py (import)',
            'status': 'ERROR',
            'error': str(e)
        })
    
    # ===== test_api_endpoints.py =====
    try:
        import test_api_endpoints
        
        test_classes = [
            test_api_endpoints.TestAPIEndpoints,
            test_api_endpoints.TestAPIValidation,
        ]
        
        results = run_test_module("test_api_endpoints.py", test_classes)
        all_results.extend(results)
        
    except Exception as e:
        print(f"  [ERROR] Failed to load test_api_endpoints.py: {e}")
        all_results.append({
            'name': 'test_api_endpoints.py (import)',
            'status': 'ERROR',
            'error': str(e)
        })

    # ===== test_custom_strategies.py =====
    try:
        import test_custom_strategies
        
        test_classes = [
            test_custom_strategies.TestCustomStrategies,
        ]
        
        results = run_test_module("test_custom_strategies.py", test_classes)
        all_results.extend(results)
        
    except Exception as e:
        print(f"  [ERROR] Failed to load test_custom_strategies.py: {e}")
        all_results.append({
            'name': 'test_custom_strategies.py (import)',
            'status': 'ERROR',
            'error': str(e)
        })

    # ===== test_custom_api_endpoints.py =====
    try:
        import test_custom_api_endpoints
        
        test_classes = [
            test_custom_api_endpoints.TestCustomAPI,
        ]
        
        results = run_test_module("test_custom_api_endpoints.py", test_classes)
        all_results.extend(results)
        
    except Exception as e:
        print(f"  [ERROR] Failed to load test_custom_api_endpoints.py: {e}")
        all_results.append({
            'name': 'test_custom_api_endpoints.py (import)',
            'status': 'ERROR',
            'error': str(e)
        })

    # ===== Summary =====
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("TEST SUMMARY")
    
    # Count by status
    passed = sum(1 for r in all_results if r['status'] == 'PASS')
    failed = sum(1 for r in all_results if r['status'] == 'FAIL')
    errors = sum(1 for r in all_results if r['status'] == 'ERROR')
    skipped = sum(1 for r in all_results if r['status'] == 'SKIP')
    total = len(all_results)
    
    print(f"  Total Tests: {total}")
    print(f"  Passed:      {passed} \033[92m({passed}/{total})\033[0m")
    print(f"  Failed:      {failed} \033[91m({failed}/{total})\033[0m" if failed else f"  Failed:      {failed}")
    print(f"  Errors:      {errors} \033[91m({errors}/{total})\033[0m" if errors else f"  Errors:      {errors}")
    print(f"  Skipped:     {skipped} \033[93m({skipped}/{total})\033[0m" if skipped else f"  Skipped:     {skipped}")
    print(f"  Duration:    {duration:.2f}s")
    
    # Failed tests detail
    failed_tests = [r for r in all_results if r['status'] in ('FAIL', 'ERROR')]
    if failed_tests:
        print_header("FAILED TESTS DETAIL", '-')
        for r in failed_tests:
            print(f"\n  {r['name']}")
            print(f"  Status: {r['status']}")
            if r['error']:
                print(f"  Error: {r['error']}")
    
    # Final status
    print()
    if failed == 0 and errors == 0:
        print("\033[92m" + "="*70 + "\033[0m")
        print("\033[92m  ALL TESTS PASSED!\033[0m")
        print("\033[92m" + "="*70 + "\033[0m")
        return True
    else:
        print("\033[91m" + "="*70 + "\033[0m")
        print(f"\033[91m  {failed + errors} TEST(S) FAILED\033[0m")
        print("\033[91m" + "="*70 + "\033[0m")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
