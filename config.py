"""
Mining Management API - Configuration File
Cấu hình tập trung cho ứng dụng
"""

# ==================== Server Configuration ====================
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9098
DEBUG_MODE = False  # Set True for development

# ==================== Logging Configuration ====================
# Flask access logs (127.0.0.1 - - [date] "GET /api/status HTTP/1.1" 200)
ENABLE_FLASK_ACCESS_LOGS = False  # Set True to enable Flask request logs

# Application logs (mining status, errors, etc.)
ENABLE_APP_LOGS = True  # Mining operations logs
ENABLE_MONITOR_LOGS = True  # Periodic mining status logs
ENABLE_DEBUG_LOGS = False  # Debug/verbose logs

# ==================== Mining Configuration ====================
# Auto-start miners on server startup
AUTO_START_ON_BOOT = True

# Hash rate monitoring interval (seconds)
HASH_RATE_CHECK_INTERVAL = 5

# Monitor status print interval (seconds)
MONITOR_STATUS_INTERVAL = 30

# ==================== Process Management ====================
# Graceful shutdown timeouts
SIGINT_WAIT_TIME = 2  # Wait after first SIGINT (seconds)
SIGINT_RETRY_COUNT = 4  # Number of SIGINT retries
SIGTERM_WAIT_TIME = 3  # Wait after SIGTERM (seconds)

# ==================== File Download ====================
CDN_BASE_URL = 'http://cdn.dndvina.com/minings'
DOWNLOAD_CHUNK_SIZE = 8192  # bytes
DOWNLOAD_TIMEOUT = 300  # seconds

# ==================== Paths ====================
MINERS_DIR = 'miners'  # Base directory for all miners

# ==================== API Configuration ====================
# CORS (Cross-Origin Resource Sharing)
ENABLE_CORS = True  # Allow cross-origin requests

# Request size limits
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
