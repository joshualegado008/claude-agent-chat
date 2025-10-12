#!/usr/bin/env python3
"""
Test Setup - Validates that your Anthropic API setup is working correctly

Run this before using the refactored agent_runner.py to ensure:
1. API key is set
2. Anthropic SDK is installed
3. Agent files exist
4. Basic API calls work
"""

import os
import sys
from pathlib import Path

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed yet, that's ok


def test_imports():
    """Test that required packages are installed"""
    print("🔍 Testing imports...")

    try:
        import anthropic
        print("   ✅ anthropic package installed")
    except ImportError:
        print("   ❌ anthropic package NOT installed")
        print("      Run: pip install anthropic")
        return False

    try:
        import yaml
        print("   ✅ pyyaml package installed")
    except ImportError:
        print("   ❌ pyyaml package NOT installed")
        print("      Run: pip install pyyaml")
        return False

    try:
        import colorama
        print("   ✅ colorama package installed")
    except ImportError:
        print("   ❌ colorama package NOT installed")
        print("      Run: pip install colorama")
        return False

    try:
        import dotenv
        print("   ✅ python-dotenv package installed")
    except ImportError:
        print("   ❌ python-dotenv package NOT installed")
        print("      Run: pip install python-dotenv")
        return False

    return True


def test_api_key():
    """Test that API key is set"""
    print("\n🔍 Testing API key...")

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("   ❌ ANTHROPIC_API_KEY environment variable NOT set")
        print("\n   To fix this:")
        print("   1. Get your API key from: https://console.anthropic.com/settings/keys")
        print("   2. Create a .env file: cp .env.example .env")
        print("   3. Add your key to .env: ANTHROPIC_API_KEY=sk-ant-...")
        print("   OR set it in your shell: export ANTHROPIC_API_KEY='sk-ant-...'")
        return False

    if not api_key.startswith('sk-ant-'):
        print(f"   ⚠️  API key doesn't start with 'sk-ant-' (found: {api_key[:10]}...)")
        print("      Make sure you're using a valid Anthropic API key")
        return False

    print(f"   ✅ API key is set ({api_key[:15]}...)")
    return True


def test_agent_files():
    """Test that agent configuration files exist"""
    print("\n🔍 Testing agent files...")

    agent_a = Path('.claude/agents/agent_a.md')
    agent_b = Path('.claude/agents/agent_b.md')

    if not agent_a.exists():
        print(f"   ❌ Agent A file not found: {agent_a}")
        return False
    print(f"   ✅ Agent A found: {agent_a}")

    if not agent_b.exists():
        print(f"   ❌ Agent B file not found: {agent_b}")
        return False
    print(f"   ✅ Agent B found: {agent_b}")

    return True


def test_api_connection():
    """Test actual API connection"""
    print("\n🔍 Testing API connection...")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

        # Make a minimal API call
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=20,
            messages=[{"role": "user", "content": "Say 'test successful' in 2 words"}]
        )

        # Extract response
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        print(f"   ✅ API connection successful!")
        print(f"   📝 Response: {response_text.strip()}")
        print(f"   💰 Tokens used: {response.usage.input_tokens + response.usage.output_tokens}")

        return True

    except Exception as e:
        print(f"   ❌ API connection failed: {str(e)}")
        return False


def test_config():
    """Test that config.yaml exists and is valid"""
    print("\n🔍 Testing config.yaml...")

    config_file = Path('config.yaml')
    if not config_file.exists():
        print(f"   ❌ config.yaml not found")
        return False

    try:
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)

        # Check for required sections
        if 'agents' not in config:
            print("   ❌ config.yaml missing 'agents' section")
            return False

        print(f"   ✅ config.yaml is valid")
        print(f"   📋 Found {len(config.get('agents', {}))} agent(s) configured")

        return True

    except Exception as e:
        print(f"   ❌ Error reading config.yaml: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Testing Anthropic API Setup")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("API Key", test_api_key),
        ("Agent Files", test_agent_files),
        ("Config File", test_config),
        ("API Connection", test_api_connection)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n   ❌ Unexpected error in {name}: {str(e)}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! You're ready to run coordinator.py")
        print("\nNext steps:")
        print("  1. Run: python3 coordinator.py --prompt \"Your question here\"")
        print("  2. Or run: python3 coordinator.py (uses default prompt from config)")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before continuing.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
