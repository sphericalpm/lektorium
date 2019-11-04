
# Quickstart guide
The current implementation of the hosted authoring central supports different methods of storing configuration of site sources and execution environments. Here we will discuss only main one: everything stored in GitLab repositories and executed in docker containers.

Lektorium server needs a separate repository to store its configuration. It fetches this repository on start and uses `config.yml` from repository root as a registry of managed sites. The format of this registry file is described in a separate section at the end of this document.

Docker is used to start lektorium, reverse proxy server and lektor instances. For GitLab access, lektorium uses ssh public key authentication so one needs to generate a keypair, place private key to `containers/server/key` and configure GitLab to allow access to lektorium and websites' repositories with this key.

## Install and start
You need to create a deployment options file for you server in the `invoke.yaml` file.
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

* `server-name` host name of the hosted authoring central
* `auth`  auth0 provider configuration (described in a separate section)
* `cfg` option can be adopted with proper configuration repository path;
* `network` docker network to be used to start containers. Pay attention that it **can not** be the default docker network.
* `env` is a list of additional environment options, where GIT_MAIL and GIT_USER options are mandatory for the proper work of git client.

Deploy and start server:
```
inv -pe build run
```

Deploy and start reverse proxy:
```
inv -pe build-proxy-image run-proxy
```

## Auth0 as authentication provider
`auth` option of `invoke.yaml` configuration file consists of comma separated options of your auth0 application: domain, client id and api name. Please check auth0 documentation for more information or start lektorium **without authentication** by adding empty auth option to command line:
```
inv -pe build run --auth=''
```

## Sites configuration file

Lektorium stores configuration of managed websites in YAML format.
The file must be stored in the root of your git repo.

Below is a structure of Lektorium config file which may require changes for your configuration:

    <site_id>:
        name: <site_name>
        owner: <owner_name>
        email: <owner_email>
        gitlab:
            scheme: <gitlab_scheme>
            host: <gitlab_host>
            namespace: <gitlab_namespace>
            project: <gitlab_project_name>
        [branch: <branch_name>]
        [url: <production_url>]

### Supported settings


#### site_id
unique id of your site

:Type: ``str``

#### site_id.name
Your website name

:Type: ``str``

#### site_id.owner
website owner name

:Type: ``str``

#### site_id.email
website owner's email

:Type: ``str``

#### site_id.url
website production url

:Type: ``str``

#### site_id.branch
gitlab branch name

:Type: ``str``

#### site_id.gitlab.schema
network protocol to work with gitlab

:Type: ``str``

#### site_id.gitlab.host
gitlab host

:Type: ``str``

#### site_id.gitlab.namespace
gitlab namespace

:Type: ``str``

#### site_id.gitlab.project
gitlab project name

:Type: ``str``

### Example
Below is an example of config file which may require changes for your configuration:

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
