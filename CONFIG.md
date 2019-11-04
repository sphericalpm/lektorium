# Lektorium Configuration File

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

## Supported settings


### site_id
unique id of your site

:Type: ``str``

### site_id.name
Your website name

:Type: ``str``

### site_id.owner
website owner name

:Type: ``str``

### site_id.email
website owner's email

:Type: ``str``

### site_id.url
website production url

:Type: ``str``

### site_id.branch
gitlab branch name

:Type: ``str``

### site_id.gitlab.schema
network protocol to work with gitlab

:Type: ``str``

### site_id.gitlab.host
gitlab host

:Type: ``str``

### site_id.gitlab.namespace
gitlab namespace

:Type: ``str``

### site_id.gitlab.project
gitlab project name

:Type: ``str``

## Examples
Below is an example of config file which may require changes for your configuration:

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

