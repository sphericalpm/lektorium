AWS_PROFILE_NAME = 'lectorium-aws-deploy'
LECTOR_AWS_SERVER_NAME = 'lectorium-aws'

AWS_SHARED_CREDENTIALS_FILE_TEMPLATE = f'''
[{AWS_PROFILE_NAME}]
  aws_access_key_id = {{aws_key_id}}
  aws_secret_access_key = {{aws_secret_key}}
'''

GITLAB_CI_TEMPLATE = f'''
lectorium-aws-deploy:
  variables:
    LC_ALL: C.UTF-8
    LANG: C.UTF-8
    AWS_PROFILE: {AWS_PROFILE_NAME}
  script:
    - apk add --update python3 python3-dev libffi-dev openssl-dev build-base
    - pip3 install --upgrade lektor
    - lektor plugins add lektor-s3
    - lektor build
    - lektor deploy "{LECTOR_AWS_SERVER_NAME}"
  only:
    - master
'''

LECTOR_S3_SERVER_TEMPLATE = f'''
[servers.{LECTOR_AWS_SERVER_NAME}]
name = Lectorium AWS
enabled = yes
target = s3://{{s3_bucket_name}}
cloudfront = {{cloudfront_id}}
'''
