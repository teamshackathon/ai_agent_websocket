#!/bin/bash
if [ -n "$DEVELOP" ]; then
    export $(cat .env.develop | xargs)
else
    export $(cat .env.production | xargs)
fi
exec "$@"