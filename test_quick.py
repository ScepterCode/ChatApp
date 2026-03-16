#!/usr/bin/env python
"""
Quick test runner for individual components.
Usage:
    python test_quick.py auth     # Test authentication
    python test_quick.py chat     # Test chat functionality  
    python test_quick.py ai       # Test AI engines
    python test_quick.py all      # Test everything
"""
import os
import sys
import django

def run_specific_tests(component):
    """Run tests for a specific component."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    test_map = {
        'auth': ['accounts.tests'],
        'chat': ['chat.tests'],
        'ai': ['ai.tests'],
        'all': ['accounts.tests', 'chat.tests', 'ai.tests']
    }
    
    if component not in test_map:
        print(f"❌ Unknown component: {component}")
        print("Available options: auth, chat, ai, all")
        sys.exit(1)
    
    test_modules = test_map[component]
    
    print(f"🧪 Running {component.upper()} tests...")
    print("=" * 40)
    
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed in {component}")
        sys.exit(1)
    else:
        print(f"\n✅ All {component} tests passed!")
        sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python test_quick.py [auth|chat|ai|all]")
        sys.exit(1)
    
    component = sys.argv[1].lower()
    run_specific_tests(component)