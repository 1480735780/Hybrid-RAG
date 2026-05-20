"""
Setup script for Enterprise Ops Assistant.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"{description} - Done")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} - Failed: {e}")
        return False


def setup_project():
    """Setup the project."""
    print("=" * 60)
    print("Enterprise Ops Assistant - Setup")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 10):
        print("Error: Python 3.10+ is required")
        sys.exit(1)

    # Create necessary directories
    directories = [
        "logs/app",
        "logs/access",
        "knowledge_base/uploads",
        "knowledge_base/processed",
        "chroma_db",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("Failed to install dependencies")
        sys.exit(1)

    # Copy .env file if not exists
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("\nCreated .env file from .env.example")
        print("Please edit .env file with your configuration")

    print("\n" + "=" * 60)
    print("Setup completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start the backend: uvicorn backend.app.main:app --reload")
    print("3. Start the frontend: streamlit run frontend/app.py")


if __name__ == "__main__":
    setup_project()
