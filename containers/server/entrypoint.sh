#!/bin/sh
set -xe
ssh-keyscan "$GIT_SERVER" >>/root/.ssh/known_hosts
[ -n "$GIT_MAIL" ] || (>&2 echo "empty GIT_MAIL" && false)
[ -n "$GIT_USER" ] || (>&2 echo "empty GIT_USER" && false)
git config --global user.email "$GIT_MAIL"
git config --global user.name "$GIT_USER"
exec /env/bin/python -m lektorium "$@"
