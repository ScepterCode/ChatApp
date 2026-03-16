#!/usr/bin/env python
"""
Run Daphne ASGI server for Django Channels support.
This starts the server with both HTTP and WebSocket support.
"""
import os
import sys
import django

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Setup Django
django.setup()

# Import and run Daphne
from daphne.cli import CommandLineInterface

if __name__ == '__main__':
    args = ['-b', '0.0.0.0', '-p', '8000', 'core.asgi:application']
    CommandLineInterface().run(args)
