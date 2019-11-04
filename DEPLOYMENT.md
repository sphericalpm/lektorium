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

You need to put private ssh key to `containers/server/key` file.

Deploy and start server:
```
inv -pe build run
```

Deploy and start reverse proxy:
```
inv -pe build-proxy-image run-proxy
```
