"""Test runner service implementation.

This module implements test execution functionality.
It provides:
- Test discovery
- Test execution
- Result collection
- Report generation
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Type, Union
import importlib
import inspect
import os
import sys
import time
import traceback

from src.domain.services.common.base import BaseService

class TestRunnerService(BaseService):
    """Service for running tests.
    
    This service is responsible for:
    - Finding tests
    - Running tests
    - Collecting results
    - Generating reports
    """
    
    def __init__(
        self,
        test_path: str,
        pattern: str = "test_*.py",
        parallel: bool = False,
        timeout: int = 60
    ):
        """Initialize test runner.
        
        Args:
            test_path: Path to test files
            pattern: Test file pattern
            parallel: Run tests in parallel
            timeout: Test timeout in seconds
        """
        super().__init__()
        self._test_path = test_path
        self._pattern = pattern
        self._parallel = parallel
        self._timeout = timeout
        
        # Test tracking
        self._tests: Dict[str, callable] = {}
        self._results: Dict[str, Dict] = {}
        self._current: Optional[str] = None
    
    def discover_tests(self) -> List[str]:
        """Find test files and methods.
        
        Returns:
            List of test names
            
        Raises:
            ValueError: If discovery fails
        """
        self._log_entry("discover_tests")
        
        try:
            # Clear existing
            self._tests.clear()
            
            # Find test files
            for root, _, files in os.walk(self._test_path):
                for file in files:
                    if not file.startswith("test_"):
                        continue
                    
                    if not file.endswith(".py"):
                        continue
                    
                    # Import module
                    module_path = os.path.join(root, file)
                    module_name = os.path.splitext(file)[0]
                    spec = importlib.util.spec_from_file_location(
                        module_name,
                        module_path
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find test methods
                    for name, member in inspect.getmembers(module):
                        if not name.startswith("test_"):
                            continue
                            
                        if not callable(member):
                            continue
                            
                        # Store test
                        full_name = f"{module_name}.{name}"
                        self._tests[full_name] = member
            
            test_names = list(self._tests.keys())
            self._log_exit("discover_tests", test_names)
            return test_names
            
        except Exception as e:
            self._log_error("discover_tests", e)
            raise ValueError(f"Test discovery failed: {str(e)}")
    
    def run_tests(
        self,
        tests: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """Run specified tests.
        
        Args:
            tests: Optional test names to run
            
        Returns:
            Test results
            
        Raises:
            ValueError: If execution fails
        """
        self._log_entry("run_tests", tests=tests)
        
        try:
            # Clear results
            self._results.clear()
            
            # Get tests to run
            to_run = tests or list(self._tests.keys())
            
            if self._parallel:
                self._run_parallel(to_run)
            else:
                self._run_sequential(to_run)
            
            self._log_exit("run_tests", self._results)
            return self._results
            
        except Exception as e:
            self._log_error("run_tests", e)
            raise ValueError(f"Test execution failed: {str(e)}")
    
    def get_report(
        self,
        format: str = "text"
    ) -> str:
        """Generate test report.
        
        Args:
            format: Report format
            
        Returns:
            Test report
            
        Raises:
            ValueError: If generation fails
        """
        self._log_entry("get_report", format=format)
        
        try:
            if format == "text":
                report = self._text_report()
            elif format == "json":
                report = self._json_report()
            else:
                raise ValueError(f"Unknown format: {format}")
            
            self._log_exit("get_report")
            return report
            
        except Exception as e:
            self._log_error("get_report", e)
            raise ValueError(f"Report generation failed: {str(e)}")
    
    def _run_sequential(
        self,
        tests: List[str]
    ) -> None:
        """Run tests sequentially.
        
        Args:
            tests: Tests to run
        """
        for test in tests:
            self._run_test(test)
    
    def _run_parallel(
        self,
        tests: List[str]
    ) -> None:
        """Run tests in parallel.
        
        Args:
            tests: Tests to run
        """
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._run_test, test)
                for test in tests
            ]
            concurrent.futures.wait(futures)
    
    def _run_test(
        self,
        test: str
    ) -> None:
        """Run single test.
        
        Args:
            test: Test to run
        """
        self._current = test
        start = time.time()
        
        try:
            # Get test method
            method = self._tests[test]
            
            # Run test
            method()
            
            # Record success
            self._results[test] = {
                "status": "passed",
                "duration": time.time() - start
            }
            
        except Exception as e:
            # Record failure
            self._results[test] = {
                "status": "failed",
                "duration": time.time() - start,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            
        finally:
            self._current = None
    
    def _text_report(self) -> str:
        """Generate text report.
        
        Returns:
            Text report
        """
        lines = []
        
        # Summary
        total = len(self._results)
        passed = sum(1 for r in self._results.values() if r["status"] == "passed")
        failed = total - passed
        
        lines.append("Test Results")
        lines.append("-" * 80)
        lines.append(f"Total: {total}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append("")
        
        # Details
        for test, result in self._results.items():
            lines.append(f"{test}: {result['status']}")
            lines.append(f"Duration: {result['duration']:.2f}s")
            
            if result["status"] == "failed":
                lines.append("Error:")
                lines.append(result["error"])
                lines.append("Traceback:")
                lines.append(result["traceback"])
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _json_report(self) -> str:
        """Generate JSON report.
        
        Returns:
            JSON report
        """
        import json
        
        return json.dumps(
            self._results,
            indent=2
        )
