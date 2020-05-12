from datetime import datetime

import boto3
import pytest
from botocore.stub import ANY, Stubber

from lektorium.aws import AWS, BUCKET_POLICY_TEMPLATE


def test_create_s3_bucket():
    bucket_name = AWS.S3_PREFIX + 'foo'
    stub_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    expected_params = {'Bucket': bucket_name}

    client = boto3.client('s3')
    stubber = Stubber(client)
    stubber.add_response('create_bucket', stub_response, expected_params)

    aws = AWS()
    aws.s3_client = client
    with stubber:
        response = aws.create_s3_bucket('foo')

    assert response == bucket_name


def test_open_bucket_access():
    bucket_name = AWS.S3_PREFIX + 'foo'
    stub_response = {'ResponseMetadata': {'HTTPStatusCode': 204}}
    expected_params_1 = {'Bucket': bucket_name}
    expected_params_2 = {
        'Bucket': bucket_name,
        'Policy': BUCKET_POLICY_TEMPLATE.format(bucket_name=bucket_name),
    }

    client = boto3.client('s3')
    stubber = Stubber(client)
    stubber.add_response(
        'delete_public_access_block',
        stub_response,
        expected_params_1,
    )
    stubber.add_response(
        'put_bucket_policy',
        stub_response,
        expected_params_2,
    )

    aws = AWS()
    aws.s3_client = client
    with stubber:
        aws.open_bucket_access(bucket_name)


def test_open_bucket_access_timeout():
    bucket_name = AWS.S3_PREFIX + 'foo'
    stub_response = {'ResponseMetadata': {'HTTPStatusCode': 404}}
    expected_params_1 = {'Bucket': bucket_name}

    client = boto3.client('s3')
    stubber = Stubber(client)
    stubber.add_response(
        'delete_public_access_block',
        stub_response,
        expected_params_1,
    )

    aws = AWS()
    aws.s3_client = client
    aws.SLEEP_TIMEOUT = 0.01
    with pytest.raises(Exception):
        with stubber:
            aws.open_bucket_access(bucket_name)


def test_create_cloudfront_distribution():
    bucket_name = AWS.S3_PREFIX + 'foo'
    bucket_origin_name = bucket_name + AWS.S3_SUFFIX
    distribution_id = 'bar'
    domain_name = 'buzz'
    stub_response = {
        'ResponseMetadata': {'HTTPStatusCode': 201},
        'Distribution': {
            'Id': distribution_id,
            'DomainName': domain_name,
            'ARN': '',
            'Status': '',
            'LastModifiedTime': datetime.now(),
            'InProgressInvalidationBatches': 1,
            'ActiveTrustedSigners': {'Quantity': 0, 'Enabled': False},
            'DistributionConfig': {
                'CallerReference': '',
                'Origins': {'Quantity': 1, 'Items': [{
                    'Id': 'target',
                    'DomainName': '',
                    'S3OriginConfig': {'OriginAccessIdentity': ''},
                }]},
                'DefaultCacheBehavior': {
                    'TargetOriginId': '',
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'all'},
                    },
                    'TrustedSigners': {'Quantity': 0, 'Enabled': False},
                    'ViewerProtocolPolicy': '',
                    'MinTTL': 1,
                },
                'Comment': '',
                'Enabled': True,
                'CustomErrorResponses': {
                    'Quantity': 1,
                    'Items': [{
                        'ErrorCode': 404,
                        'ResponsePagePath': '/404.html',
                        'ResponseCode': '404',
                        'ErrorCachingMinTTL': 60,
                    }],
                },
            },
        },
    }

    expected_params = dict(
        DistributionConfig=dict(
            CallerReference=ANY,
            Comment=ANY,
            Enabled=True,
            DefaultRootObject='index.html',
            Origins=dict(
                Quantity=1,
                Items=[dict(
                    Id=ANY,
                    DomainName=bucket_origin_name,
                    S3OriginConfig=dict(OriginAccessIdentity=ANY),
                )]
            ),
            DefaultCacheBehavior=dict(
                TargetOriginId=ANY,
                ViewerProtocolPolicy='redirect-to-https',
                TrustedSigners=dict(Quantity=0, Enabled=False),
                ForwardedValues=dict(
                    Cookies={'Forward': 'all'},
                    Headers=dict(Quantity=0),
                    QueryString=False,
                    QueryStringCacheKeys=dict(Quantity=0),
                ),
                MinTTL=ANY,
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
        )
    )

    client = boto3.client('cloudfront')
    stubber = Stubber(client)
    stubber.add_response('create_distribution', stub_response, expected_params)

    aws = AWS()
    aws.cloudfront_client = client
    with stubber:
        response = aws.create_cloudfront_distribution(bucket_name)

    assert response == (distribution_id, domain_name)
