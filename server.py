#!/usr/bin/env python3
"""
Wrapper script for graceful shutdown handling
Prevents messy traceback when Ctrl+C during import
"""

import sys
import signal

# Set up signal handlers BEFORE any imports
def early_signal_handler(sig, frame):
    print('\n🛑 Server stopping...')
    sys.exit(0)

# Register handlers early
signal.signal(signal.SIGINT, early_signal_handler)
signal.signal(signal.SIGTERM, early_signal_handler)

# Now import and run the actual app
if __name__ == '__main__':
    try:
        # Import app.py as module
        import app
    except KeyboardInterrupt:
        print('\n🛑 Server stopped during startup')
        sys.exit(0)
    except Exception as e:
        print(f'\n❌ Error starting server: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
