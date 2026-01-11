"""Script to automatically install Playwright browsers"""

import subprocess
import sys
from utils.logging import get_logger

logger = get_logger(__name__)


def install_playwright_browsers():
    """Install Playwright browsers and dependencies"""
    try:
        logger.info("Installing Playwright browsers...")
        result = subprocess.run(
            ['playwright', 'install', '--with-deps'],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Playwright browsers installed successfully")
        logger.debug("Install output", output=result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install Playwright browsers", error=e.stderr)
        return False
    except FileNotFoundError:
        logger.error("Playwright not found. Please install: pip install playwright")
        return False


if __name__ == "__main__":
    success = install_playwright_browsers()
    sys.exit(0 if success else 1)
