#!/bin/sh
set -xe
source /etc/bin/activate
exec /env/bin/python -m lektorium "$@"
