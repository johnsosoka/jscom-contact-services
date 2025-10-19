#!/usr/bin/env python3
"""
Simple test to verify Discord template loading and rendering.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from jinja2 import Environment, FileSystemLoader

def get_mountain_timestamp() -> str:
    """Get current timestamp formatted in Mountain Time."""
    mountain_tz = ZoneInfo('America/Denver')
    now = datetime.now(mountain_tz)
    return now.strftime('%B %d, %Y at %I:%M %p MT')

def test_standard_template():
    """Test standard Discord message template."""
    print("Testing standard Discord template...")

    # Set up template environment
    template_dir = Path(__file__).parent / 'app' / 'templates' / 'discord'
    jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    # Load and render standard template
    template = jinja_env.get_template('standard_discord_message.txt')
    message = template.render(
        contact_name='John Doe',
        contact_email='john.doe@example.com',
        contact_message='This is a test message.',
        user_agent='Mozilla/5.0',
        source_ip='192.168.1.1',
        timestamp=get_mountain_timestamp()
    )

    print("Standard template rendered successfully:")
    print("-" * 50)
    print(message)
    print("-" * 50)

    # Basic assertions
    assert 'John Doe' in message
    assert 'john.doe@example.com' in message
    assert 'This is a test message.' in message
    assert 'Mozilla/5.0' in message
    assert '192.168.1.1' in message
    assert 'New Contact Message' in message
    assert ':envelope_with_arrow:' in message
    assert ':clock3:' in message
    assert 'MT' in message

    print("✓ Standard template test passed!\n")
    return True

def test_consulting_template():
    """Test consulting Discord message template."""
    print("Testing consulting Discord template...")

    # Set up template environment
    template_dir = Path(__file__).parent / 'app' / 'templates' / 'discord'
    jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    # Load and render consulting template
    template = jinja_env.get_template('consulting_discord_message.txt')
    message = template.render(
        contact_name='Jane Smith',
        contact_email='jane@company.com',
        company_name='Acme Corp',
        industry='Technology',
        contact_message='We need consulting services for our cloud migration.',
        user_agent='Mozilla/5.0',
        source_ip='10.0.0.1',
        timestamp=get_mountain_timestamp()
    )

    print("Consulting template rendered successfully:")
    print("-" * 50)
    print(message)
    print("-" * 50)

    # Basic assertions
    assert 'Jane Smith' in message
    assert 'jane@company.com' in message
    assert 'Acme Corp' in message
    assert 'Technology' in message
    assert 'cloud migration' in message
    assert 'Mozilla/5.0' in message
    assert '10.0.0.1' in message
    assert 'New Consulting Inquiry' in message
    assert ':briefcase:' in message
    assert ':clock3:' in message
    assert 'MT' in message

    print("✓ Consulting template test passed!\n")
    return True

if __name__ == '__main__':
    try:
        success = True
        success &= test_standard_template()
        success &= test_consulting_template()

        if success:
            print("=" * 50)
            print("✓ All Discord template tests passed!")
            print("=" * 50)
            sys.exit(0)
        else:
            print("✗ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
