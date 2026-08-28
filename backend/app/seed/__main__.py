"""Seed database with taxonomy, sample questions, and admin user."""

from app.seed.runner import run_seed

if __name__ == "__main__":
    run_seed()
