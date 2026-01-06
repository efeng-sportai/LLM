#!/usr/bin/env python3
"""
Test runner for SportAI backend
Run all tests or specific test files
"""

import sys
import os
import subprocess
import argparse

def run_test(test_file):
    """Run a specific test file"""
    test_path = os.path.join("tests", test_file)
    if not os.path.exists(test_path):
        print(f"ERROR: Test file {test_path} not found")
        return False
    
    print(f"Running {test_file}...")
    print("=" * 50)
    
    try:
        result = subprocess.run([sys.executable, test_path], cwd=os.getcwd())
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: Failed to run {test_file}: {e}")
        return False

def run_all_tests():
    """Run all test files"""
    test_files = [
        "test_mongodb_connection.py",
        "test_training_data.py",
        "test_complete_system.py"
    ]
    
    print("Running all SportAI backend tests...")
    print("=" * 50)
    
    results = []
    for test_file in test_files:
        success = run_test(test_file)
        results.append((test_file, success))
        print()  # Add spacing between tests
    
    # Summary
    print("=" * 50)
    print("Test Results Summary:")
    for test_file, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"  {test_file}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="SportAI Backend Test Runner")
    parser.add_argument("test", nargs="?", help="Specific test file to run (optional)")
    parser.add_argument("--populate", action="store_true", help="Populate database with test data")
    
    args = parser.parse_args()
    
    if args.populate:
        print("Populating database with test data...")
        success = run_test("populate_test_data.py")
        if success:
            print("Database populated successfully!")
        else:
            print("Database population failed!")
        return
    
    if args.test:
        # Run specific test
        success = run_test(args.test)
        if success:
            print(f"\n{args.test} PASSED!")
        else:
            print(f"\n{args.test} FAILED!")
    else:
        # Run all tests
        success = run_all_tests()
        if success:
            print("\nAll tests completed successfully!")
        else:
            print("\nSome tests failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()
