[![CircleCI](https://circleci.com/gh/sphericalpm/lektorium.svg?style=svg)](https://circleci.com/gh/sphericalpm/lektorium)
[![codecov](https://codecov.io/gh/sphericalpm/lektorium/branch/master/graph/badge.svg)](https://codecov.io/gh/sphericalpm/lektorium)

# What is Lektorium? 
Lektorium _will be_ a web content management solution for those with many little and/or similar websites. 
A typical user would be a large and loosely governed organisation with departments having a strong mandate to 
communicate externally and independently publish on the web. 

We will use Lektor (https://github.com/lektor/lektor), a great static site generator, as the source of basic content management and organisation functionality, and augment it with everything necessary for the business setting described above. 

# Design goals
If you are responsible for the web presence, corporate branding, design and consistency in communications in an organisation 
described above - may the Universe afford you the best of luck, for keeping such arrangements from becoming an uncontrollable 
zoo of technologies and designs is not easy. Lektorium should help you address some of the related pains. Our plan is: 

## 1. Separate "nerds" and "dummies"
Some users will believe that they need to modify templates, create their own CSS and JavaScript. This is totally fine. 
These _nerds_ will have direct access to the _theme_ repository and will be made responsible for the changes they make. 
Other users will only ever need to change content. These _dummies_ will have a friendly user interface that will guide them. 

## 2. All state in the repository
The only configuration or state living outside the repository is the location and credentials for the repository. 
**All** other state, config, content or anything that is expected to survive unplugging of the machine is stored in the code repository. 
Multi-user scenarios, such as collaborative content authoring, will be resolved using repository means even if _dummies_ are involved. 
In case of conflicts, a _nerd_ will be called in. 

## 3. No server-side code 
Server-side code is only interacted with using XHRs and it always speaks data, never presentation or user interaction. 
I.e. server side code will never be redirected to, produce HTML code or responses to be interpreted by the browser 
(as opposed to the users' JavaScript code). 

Server-side code is not a concern of Lektorium. Related attack vectors are made completely impossible because everything 
we are dealing with is static. Server resource issues are gone because all code is executed on the client. 

## 4. Service administrators should not have to be nerds
It should be possible to create and publish new websites, and carry out other site lifecycle using simple web interfaces.

## 5. Other than Lektor, we don't have other loyalties
Lektorium should be resonably easy to teach to work with various webservers, repositories, DNSes, clouds... 

# What will be in the box / how will it work

The basic architecture idea is that we create two things: 

- A "provisioning portal" where admins will set up which sites we have at all, who can work on their content, what
they will be called for the outside world etc. 
- A hosted authoring system that will create pre-configured Lektor instances for unsophisticated content authors
- A plugin API to turn sites' configuration stored in a VCS into configuration of whatever necessary to host these 
sites (web server, DNS zone, S3 buckets, 0auth,... etc.)    


![Architecture idea](./architecture_idea.svg)

Admins will add a site using the provisioning portal. The portal will create a repo for the site, grant access and trigger
update of whatever configs that need to be updated via the config plugins. 

Nerds will be granted access to the site's repo directly. 

Dummies will be restricted to the use of hosted authoring. All changes from the hosted authoring will be committed into 
the VCS and picked up for promotion to whatever environment by the CI. 


---
# Setting up automatic Lector deployment into AWS infrastructure using gitlab CI/CD pipelines

## Prepare AWS

### Create S3 bucket and Cloudfront

This step will be automated in lectorium

A guide can be used to create S3 [bucket](https://docs.aws.amazon.com/AmazonS3/latest/dev/website-hosting-custom-domain-walkthrough.html) and [cloudfront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html#HowCloudFrontWorksOverview)
Make note of bucket's and Cloudfront's names as they will be used in Lector's config

### Create a user for S3 and Cloudfront access

For deploying lector to S3 there must exist a user whose credentials will be used

* Open [IAM](https://console.aws.amazon.com/iam/home#/home)
* Click on Users in the sidebar
* Click "Add user"
* Give user a name and "Programmatic access"
* Give user access to S3 and Cloudfront (presets can be used)
* Open newly created user and select "Security credentials" tab
* Click Create Access Key
* Click Show User Security Credentials

## Prepare gitlab

### Create environment

* Open project
* Go to Settings -> CI/CD
* Add variable of type `File` and key `AWS_SHARED_CREDENTIALS_FILE`
* The value of this variable should contain the following data (replace `KEY_ID` and `SECRET_KEY` with the ones from created AWS user):
```
[lectorium-aws-deploy]
aws_access_key_id = <KEY_ID>
aws_secret_access_key = <SECRET_KEY>
```
### Make sure to have a runner

Gitlab instance should have a runner [installed](https://docs.gitlab.com/runner/install/) to execute pipeline jobs.

It is convenient to use docker for a runner. A docker runner can be created with a command:
`docker run --rm -t -i -v gitlab-runner-config:/etc/gitlab-runner gitlab/gitlab-runner register`
This will launch a wizard that will [register](https://docs.gitlab.com/runner/register/) a runner.
Recommended options are: `alpine:latest` as image and `docker` as executor.

After that, a docker container can be run with command:
`docker run -d --restart=unless-stopped -v gitlab-runner-config:/etc/gitlab-runner -v /var/run/docker.sock:/var/run/docker.sock gitlab/gitlab-runner run`

## Update Lector project

### Update lector project file

In Lector config (`www.lektorproject`) add a section (substituning `NAME_OF_AWS_BUCKET` and `CLOUDFRONT_ID` with appropriate values)
```
[servers.lectorium-aws-deploy]
name = Lectorium AWS Deploy
enabled = yes
target = s3://<NAME_OF_AWS_BUCKET>
cloudfront = <CLOUDFRONT_ID>
```
This will tell `lector-s3` plugin where to deploy the project.

### Add gitlab ci file

In the root of Lectorium project create a file `.gitlab-ci.yml` containing the following code:
```yaml
lectorium-aws-deploy:
  variables:
    LC_ALL: C.UTF-8
    LANG: C.UTF-8
    AWS_PROFILE: lectorium-aws-deploy
  script:
    - apk add --update python3 python3-dev libffi-dev openssl-dev build-base
    - pip3 install --upgrade lektor
    - lektor plugins add lektor-s3
    - lektor build
    - lektor deploy "lectorium-aws-deploy"
  only:
    - master
```
Section `only` contains a name of the branch that should trigger deployment script when changed.
This script will install lector and lector-s3 in a container, build the project and deploy it to AWS.
