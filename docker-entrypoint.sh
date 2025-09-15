#!/bin/sh
set -e

# Ensure all required media directories exist
# Note: We don't set permissions here since /app is mounted as a volume from host
# and we cannot change permissions on mounted host directories from container
mkdir -p /app/media/uploads/user

# Execute the command passed to the entrypoint
exec "$@"
