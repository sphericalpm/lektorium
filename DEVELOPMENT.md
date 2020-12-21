# TDD with real gitlab
Module `test_gitlab_real.py` contains helpers to do TDD with real gitlab.
To use it you need to run test suite with `LEKTORIUM_GITLAB_TEST` environment
varibale provided. This variable whould be formatted as `[<key>=<value>:]<key>=<value>`.
Possible keys are:
* scheme=<http|https>
* host=<gitlab host>
* config=<path with namespace to lektorium config repository>
* token=<gitlab access token>
