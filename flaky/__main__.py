"""
Entry point for running flaky as a module.

Usage:
    python -m flaky run --case my_agent --runs 50
"""

from flaky.runner import main

if __name__ == "__main__":
    main()
