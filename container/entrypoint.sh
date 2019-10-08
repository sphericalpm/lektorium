#!/bin/sh
ssh-keyscan gitlab >>/root/.ssh/known_hosts
exec /env/bin/python -m lektorium "$@"
