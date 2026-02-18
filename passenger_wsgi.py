"""
Passenger WSGI file for cPanel deployment
This file is required by cPanel's Python application handler (Passenger)
"""

import sys
import os

# ============================================================================
# IMPORTANT: Update these paths for your cPanel account
# ============================================================================

# Path to your virtual environment Python interpreter
# Find this in cPanel under "Setup Python App" after creating the app
# Example: /home/yourusername/virtualenv/pytrends_api/3.8/bin/python3
INTERP = "/home/propxtur/virtualenv/pytrends_api/3.8/bin/python3"

# Your cPanel username - REPLACE THIS
CPANEL_USERNAME = "propxtur"

# ============================================================================
# Virtual Environment Setup
# ============================================================================

# Ensure we're using the virtual environment Python
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add application directory to Python path
app_path = os.path.join('/home', CPANEL_USERNAME, 'pytrends_api')
sys.path.insert(0, app_path)

# ============================================================================
# Environment Variables
# ============================================================================

# SECURITY: Set your API secret key here
# Generate a strong key using: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
os.environ['API_SECRET_KEY'] = 'CmgEDvH-O5JVmsXcE7Nci5Qv22suJJ74Gq8k3Y9NlDc'

# Optional: Set other environment variables
# os.environ['LOG_LEVEL'] = 'INFO'
# os.environ['TZ'] = 'UTC'

# ============================================================================
# Import Application
# ============================================================================

try:
    # Import the FastAPI app
    # The 'app' variable from pytrends_api.py becomes 'application' for Passenger
    from pytrends_api import app as application
    
    # Log successful import (optional, for debugging)
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Passenger WSGI: FastAPI application loaded successfully")
    
except Exception as e:
    # If import fails, create a simple error application
    import logging
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import application: {e}", exc_info=True)
    
    # Create a minimal error response app
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = b'Application failed to load. Check error logs.'
        
        response_headers = [
            ('Content-type', 'text/plain'),
            ('Content-Length', str(len(output)))
        ]
        
        start_response(status, response_headers)
        return [output]

# ============================================================================
# Passenger Configuration
# ============================================================================

# This ensures Passenger can find the application
if __name__ == '__main__':
    # This block won't be executed by Passenger, but useful for testing
    print("This file is meant to be run by Passenger/cPanel")
    print("To test locally, use: python pytrends_api.py")
