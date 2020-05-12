from time import sleep
from uuid import uuid4

import boto3
from cached_property import cached_property


BUCKET_POLICY_TEMPLATE = '''{{
    "Version": "2012-10-17",
    "Statement": [{{
        "Sid": "PublicReadGetObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::{bucket_name}/*"
    }}]
}}
'''


class AWS:
    S3_PREFIX = 'lektorium-'
    S3_SUFFIX = 'amazonaws.com'
    SLEEP_TIMEOUT = 2

    @cached_property
    def s3_client(self):
        return boto3.client('s3')

    @cached_property
    def cloudfront_client(self):
        return boto3.client('cloudfront')

    @staticmethod
    def _get_status(response):
        return response.get('ResponseMetadata', {}).get('HTTPStatusCode', -1)

    @staticmethod
    def _raise_if_not_status(response, response_code, error_text):
        if AWS._get_status(response) != response_code:
            raise Exception(error_text)

    def create_s3_bucket(self, site_id, prefix=''):
        prefix = prefix or self.S3_PREFIX
        bucket_name = prefix + site_id
        response = self.s3_client.create_bucket(Bucket=bucket_name)
        self._raise_if_not_status(
            response, 200,
            'Failed to create S3 bucket',
        )
        return bucket_name

    def open_bucket_access(self, bucket_name):
        # Bucket may fail to be created and registered at this moment
        # Retry a few times and wait a bit in case bucket is not found
        for _ in range(3):
            response = self.s3_client.delete_public_access_block(Bucket=bucket_name)
            response_code = self._get_status(response)
            if response_code == 404:
                sleep(self.SLEEP_TIMEOUT)
            elif response_code == 204:
                break
            else:
                raise Exception('Failed to remove bucket public access block')

        response = self.s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=BUCKET_POLICY_TEMPLATE.format(bucket_name=bucket_name),
        )
        self._raise_if_not_status(
            response, 204,
            'Failed to set bucket access policy',
        )

        response = self.s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration=dict(
                ErrorDocument=dict(
                    Key='error.html',
                ),
                IndexDocument=dict(
                    Suffix='index.html',
                ),
            )
        )
        self._raise_if_not_status(
            response, 200,
            'Failed to make S3 bucket website',
        )

    def create_cloudfront_distribution(self, bucket_name):
        region = self.s3_client.meta.region_name
        domain = f'{bucket_name}.s3-website-{region}.{self.S3_SUFFIX}'
        response = self.cloudfront_client.create_distribution(
            DistributionConfig=dict(
                CallerReference=str(uuid4()),
                Comment='Lektorium',
                Enabled=True,
                DefaultRootObject='index.html',
                Origins=dict(
                    Quantity=1,
                    Items=[dict(
                        Id='1',
                        DomainName=domain,
                        S3OriginConfig=dict(OriginAccessIdentity=''),
                    )]
                ),
                DefaultCacheBehavior=dict(
                    TargetOriginId='1',
                    ViewerProtocolPolicy='redirect-to-https',
                    TrustedSigners=dict(Quantity=0, Enabled=False),
                    ForwardedValues=dict(
                        Cookies={'Forward': 'all'},
                        Headers=dict(Quantity=0),
                        QueryString=False,
                        QueryStringCacheKeys=dict(Quantity=0),
                    ),
                    MinTTL=1000,
                ),
                CustomErrorResponses=dict(
                    Quantity=1,
                    Items=[dict(
                        ErrorCode=404,
                        ResponsePagePath='/404.html',
                        ResponseCode='404',
                        ErrorCachingMinTTL=60,
                    )],
                ),
            ))
        self._raise_if_not_status(
            response, 201,
            'Failed to create CloudFront distribution',
        )
        distribution_data = response['Distribution']
        return distribution_data['Id'], distribution_data['DomainName']
