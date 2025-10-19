"""
Test runner for the Eir STPA Tool test suite
"""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from tests.test_constants import TestConstants
from tests.test_validation import TestInputValidator, TestValidationError
from tests.test_models import (
    TestState, TestSystemNode, TestControlLink, TestLoss, TestHazard,
    TestUnsafeControlAction, TestControlStructure, TestSTPAModel, TestIDGenerator
)
from tests.test_file_io import TestSTPAModelIO
from tests.test_ui_integration import (
    TestUIValidation, TestConstants as TestUIConstants,
    TestErrorHandling, TestMemoryManagement
)
from tests.test_ai_integration import TestAIIntegration, TestAIIntegrationLive
from tests.test_config import (
    TestPathConfig, TestUIConfig, TestAIConfig, TestPerformanceConfig,
    TestDevelopmentConfig, TestEirConfig, TestConfigGlobals
)
from tests.test_logging_config import (
    TestEirLogFormatter, TestPerformanceLogFilter, TestLoggingContext,
    TestLoggingFunctions, TestLoggerIntegration
)


def create_test_suite():
    """Create a comprehensive test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        # Core module tests
        TestConstants,
        TestInputValidator,
        TestValidationError,
        TestState,
        TestSystemNode,
        TestControlLink,
        TestLoss,
        TestHazard,
        TestUnsafeControlAction,
        TestControlStructure,
        TestSTPAModel,
        TestIDGenerator,
        TestSTPAModelIO,
        
        # Configuration tests
        TestPathConfig,
        TestUIConfig,
        TestAIConfig,
        TestPerformanceConfig,
        TestDevelopmentConfig,
        TestEirConfig,
        TestConfigGlobals,
        
        # Logging tests
        TestEirLogFormatter,
        TestPerformanceLogFilter,
        TestLoggingContext,
        TestLoggingFunctions,
        TestLoggerIntegration,
        
        # UI integration tests
        TestUIValidation,
        TestUIConstants,
        TestErrorHandling,
        TestMemoryManagement,
        
        # AI integration tests
        TestAIIntegration,
        TestAIIntegrationLive,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    return suite


def run_tests(verbosity=2):
    """Run the test suite with specified verbosity"""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOVERALL: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"{'='*60}")
    
    return success


def run_specific_tests(test_pattern):
    """Run tests matching a specific pattern"""
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern=test_pattern)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == '__main__':
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage:")
            print("  python run_tests.py              # Run all tests")
            print("  python run_tests.py --quiet      # Run with minimal output")
            print("  python run_tests.py --pattern <pattern>  # Run tests matching pattern")
            sys.exit(0)
        elif sys.argv[1] == '--quiet':
            success = run_tests(verbosity=1)
        elif sys.argv[1] == '--pattern' and len(sys.argv) > 2:
            run_specific_tests(sys.argv[2])
            sys.exit(0)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        success = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
