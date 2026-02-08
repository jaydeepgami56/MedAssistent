#!/usr/bin/env python3
"""
API Key Verification Script for MedAssist AI
Tests all API keys to ensure they are valid and working.

Usage:
    python verify_api_keys.py

Requirements:
    pip install requests python-dotenv
"""

import os
import sys
import requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Attempting to read environment variables directly...\n")


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def load_environment():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'

    if not env_file.exists():
        print_warning(f".env file not found at {env_file}")
        print_info("Create .env file by copying .env.template and filling in your API keys")
        print_info("For now, will check system environment variables only\n")
        return False

    if DOTENV_AVAILABLE:
        load_dotenv(env_file)
        print_success(f"Loaded environment variables from {env_file}\n")
        return True
    else:
        print_warning("python-dotenv not available, cannot load .env file")
        print_info("Install with: pip install python-dotenv\n")
        return False


def verify_anthropic_api_key():
    """Verify Anthropic API key by making a test API call"""
    print_header("ANTHROPIC API KEY VERIFICATION (REQUIRED)")

    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print_error("ANTHROPIC_API_KEY environment variable not set")
        print_info("Get your API key from: https://console.anthropic.com/")
        print_info("Add to .env file: ANTHROPIC_API_KEY=sk-ant-...")
        return False

    if not api_key.startswith('sk-ant-'):
        print_error(f"ANTHROPIC_API_KEY has invalid format: {api_key[:10]}...")
        print_info("Key should start with 'sk-ant-'")
        return False

    print_info(f"Testing Anthropic API key: {api_key[:15]}...{api_key[-4:]}")

    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': 'Hi'}]
            },
            timeout=10
        )

        if response.status_code == 200:
            print_success("Anthropic API key is VALID and working!")
            data = response.json()
            print_info(f"Model: {data.get('model', 'N/A')}")
            print_info(f"Response ID: {data.get('id', 'N/A')}")
            return True
        elif response.status_code == 401:
            print_error("Authentication failed - API key is invalid")
            print_info("Get a new API key from: https://console.anthropic.com/")
            return False
        elif response.status_code == 429:
            print_error("Rate limit exceeded")
            print_info("Check your usage at: https://console.anthropic.com/")
            return False
        else:
            print_error(f"API request failed with status {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Network error: {str(e)}")
        print_info("Check your internet connection")
        return False


def verify_ncbi_api_key():
    """Verify NCBI/PubMed API key"""
    print_header("NCBI/PubMed API KEY VERIFICATION (OPTIONAL)")

    api_key = os.getenv('NCBI_API_KEY')

    if not api_key:
        print_warning("NCBI_API_KEY environment variable not set")
        print_info("This is OPTIONAL for MVP but recommended for production")
        print_info("Without API key: 3 requests/second limit")
        print_info("With API key: 10 requests/second limit")
        print_info("Get your API key from: https://www.ncbi.nlm.nih.gov/account/")
        return None  # None = optional, not set

    print_info(f"Testing NCBI API key: {api_key[:8]}...{api_key[-4:]}")

    try:
        # Test with a simple PubMed search
        response = requests.get(
            'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
            params={
                'db': 'pubmed',
                'term': 'diabetes',
                'api_key': api_key,
                'retmode': 'json',
                'retmax': 1
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if 'esearchresult' in data and 'count' in data['esearchresult']:
                print_success("NCBI API key is VALID and working!")
                print_info(f"Test search returned {data['esearchresult']['count']} results")
                return True
            else:
                print_warning("Unexpected response format from NCBI API")
                print_info(f"Response: {str(data)[:200]}")
                return False
        else:
            print_error(f"NCBI API request failed with status {response.status_code}")
            print_info("Key might be invalid or there's a service issue")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Network error: {str(e)}")
        print_info("Check your internet connection")
        return False


def verify_drugbank_api_key():
    """Verify DrugBank API key"""
    print_header("DrugBank API KEY VERIFICATION (OPTIONAL - Can use mock data)")

    api_key = os.getenv('DRUGBANK_API_KEY')

    if not api_key:
        print_warning("DRUGBANK_API_KEY environment variable not set")
        print_info("This is OPTIONAL for MVP - mock data can be used for development")
        print_info("For production, get API access from: https://go.drugbank.com/")
        print_info("Academic access is FREE but requires institutional email")
        return None  # None = optional, not set

    print_info(f"Testing DrugBank API key: {api_key[:8]}...{api_key[-4:]}")
    print_warning("DrugBank API verification not implemented in this script")
    print_info("DrugBank API requires specific authentication method")
    print_info("Manual verification: Check https://docs.drugbank.com/v1/")
    print_info("For MVP, consider using USE_MOCK_DRUGBANK=true in .env")

    return None  # Cannot verify without full auth implementation


def verify_lm_studio():
    """Verify LM Studio is running"""
    print_header("LM STUDIO VERIFICATION (LOCAL AI - HIPAA Compliance)")

    base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234/v1')

    print_info(f"Checking LM Studio at: {base_url}")

    try:
        response = requests.get(f"{base_url}/models", timeout=5)

        if response.status_code == 200:
            print_success("LM Studio is running and accessible!")
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print_info(f"Available models: {len(data['data'])}")
                for model in data['data'][:3]:  # Show first 3 models
                    print_info(f"  - {model.get('id', 'Unknown')}")
            else:
                print_warning("No models loaded in LM Studio")
                print_info("Load a model in LM Studio GUI for local inference")
            return True
        else:
            print_warning(f"LM Studio responded with status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_warning("LM Studio is not running or not accessible")
        print_info("This is OPTIONAL for MVP development")
        print_info("Install LM Studio from: https://lmstudio.ai/")
        print_info("Start LM Studio and enable local server on port 1234")
        return None
    except requests.exceptions.RequestException as e:
        print_error(f"Network error: {str(e)}")
        return False


def main():
    """Main verification function"""
    print_header("MedAssist AI - API Key Verification")
    print("This script will verify all API keys needed for the project\n")

    # Load environment variables
    load_environment()

    # Track results
    results = {
        'required': [],
        'optional': []
    }

    # Verify required keys
    anthropic_result = verify_anthropic_api_key()
    results['required'].append(('Anthropic API', anthropic_result))

    # Verify optional keys
    ncbi_result = verify_ncbi_api_key()
    results['optional'].append(('NCBI API', ncbi_result))

    drugbank_result = verify_drugbank_api_key()
    results['optional'].append(('DrugBank API', drugbank_result))

    lm_studio_result = verify_lm_studio()
    results['optional'].append(('LM Studio', lm_studio_result))

    # Print summary
    print_header("VERIFICATION SUMMARY")

    print(f"{Colors.BOLD}Required API Keys:{Colors.ENDC}")
    all_required_ok = True
    for name, result in results['required']:
        if result is True:
            print_success(f"{name}: OK")
        elif result is False:
            print_error(f"{name}: FAILED")
            all_required_ok = False
        else:
            print_warning(f"{name}: NOT CONFIGURED")
            all_required_ok = False

    print(f"\n{Colors.BOLD}Optional Services:{Colors.ENDC}")
    for name, result in results['optional']:
        if result is True:
            print_success(f"{name}: OK")
        elif result is False:
            print_warning(f"{name}: CONFIGURED BUT FAILED")
        else:
            print_info(f"{name}: NOT CONFIGURED (OK for MVP)")

    # Final status
    print("\n" + "=" * 80)
    if all_required_ok:
        print_success("\n✓ All REQUIRED API keys are configured and working!")
        print_info("You can proceed with development\n")
        sys.exit(0)
    else:
        print_error("\n✗ Some REQUIRED API keys are missing or invalid")
        print_info("Fix the issues above before proceeding\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
