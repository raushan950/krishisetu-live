#!/usr/bin/env bash
# Exit on error
set -o errexit

# Build-time only: install dependencies and collect static files.
# Database migrations and demo seeding run here because Render's free web
# service does not always expose a pre-deploy/release command. This script
# runs once per deploy, not on every dyno/process restart.
pip install -r requirements.txt
python manage.py collectstatic --no-input

# Apply pending migrations. Django takes an advisory lock so concurrent
# migrate attempts from a second deploy are serialized rather than corrupting
# schema. This never drops or resets the production database.
python manage.py migrate --no-input

# Idempotent demo accounts for SIH evaluation. Existing users are not
# overwritten unless SEED_DEMO_USERS_RESET_PASSWORDS is explicitly enabled
# via `python manage.py seed_demo_users --reset-passwords`.
python manage.py seed_demo_users
