You need to create config for you server in `invoke.yaml` file.
Example config (used on test server):

```yaml
server-name: lektorium.patrushev.me
auth: ap-lektorium.eu.auth0.com,w1oxvMsFpZCW4G224I8JR7D2et9yqTYo,Lektorium
cfg: LOCAL:DOCKER,GIT=git@gitlab:apatrushev/lektorium.patrushev.me.git
network: chisel
env:
  GIT_MAIL: lektorium@lektorium.patrushev.me
  GIT_USER: Lektorium
```


[Config file documentation](/CONFIG.md)


Example `config.yml` (server configuration file to be placed in git repo):
```yaml
patrushev.me:
  email: apatrushev@gmail.com
  name: patrushev.me
  owner: Anton Patrushev
  gitlab:
    scheme: http
    host: gitlab
    namespace: apatrushev
    project: apatrushev.github.io
  branch: src
  url: https://patrushev.me
spherical-website:
  email: mv@spherical.pm
  owner: Michael Vartanyan
  gitlab:
    scheme: http
    host: gitlab
    namespace: apatrushev
    project: spherical-website
  url: https://www.spherical.pm
```

You need to put private ssh key to `containers/server/key` file.

Deploy and start server:
```
inv -pe build run
```

Deploy and start reverse proxy:
```
inv -pe build-proxy-image run-proxy
```
