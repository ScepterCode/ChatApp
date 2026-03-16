#!/usr/bin/env python
"""
Comprehensive test runner for the chat application.
"""
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

def run_tests():
    """Run all tests for the application."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    print("🧪 Running Chat Application Test Suite")
    print("=" * 50)
    print("📝 This will test:")
    print("   • Authentication endpoints (accounts)")
    print("   • Chat functionality (chat)")
    print("   • AI engines (ai)")
    print("   • Integration tests")
    print("=" * 50)
    
    # Run specific test modules
    test_modules = [
        'accounts.tests',
        'chat.tests',
        'ai.tests',
    ]
    
    failures = test_runner.run_tests(test_modules)
    
    print("\n" + "=" * 50)
    if failures:
        print(f"❌ {failures} test(s) failed")
        print("💡 Check the output above for details")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        print("🎉 Your chat application is working correctly!")
        sys.exit(0)

if __name__ == '__main__':
    run_tests()