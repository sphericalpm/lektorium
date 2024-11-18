import setuptools


setuptools.setup(
    name='lektorium',

    use_scm_version=True,
    setup_requires=[
        'setuptools_scm',
    ],

    author='Anton Patrushev',
    author_email='ap@spherical.pm',
    maintainer='spherical.pm',
    maintainer_email='support@spherical.pm',

    description=(
        'a pragmatic web content management solution '
        'for those with way too many little sites'
    ),
    license='MIT',

    packages=[
        'lektorium',
        'lektorium.repo',
        'lektorium.repo.local',
    ],
    package_dir={
        '': 'src',
    },
    package_data={
        'lektorium': [
            'client/*',
            'client/*/*',
            'client/*/*/*',
        ],
    },
    install_requires=[
        'aiodocker',
        'aiohttp-graphql<1.1',
        'aiohttp==3.10.11',
        'appdirs',
        'authlib',
        'beautifulsoup4',
        'bidict',
        'boto3',
        'cached-property',
        'graphene<3',
        'graphql-core<3',
        'graphql-server-core<1.1.2',
        'importlib-resources ; python_version < "3.7"',
        'lektor==3.2.0',
        'markupsafe==2.0.1',
        'more-itertools',
        'python-dateutil<2.8.1',
        'pyyaml',
        'spherical-dev>=0.2.2,<0.3.0',
        'wrapt',
        'invoke',
        'decorator',
        'pytz',
    ],
    extras_require={
        'dev': [
            'aiohttp-devtools',
            'aioresponses',
            'aresponses',
            'async-timeout',
            'coverage<5',
            'mypy',
            'pep8-naming',
            'pydocstyle',
            'pytest-aiohttp',
            'pytest-asyncio',
            'pytest-cov',
            'requests-mock',
            'spherical-dev[dev]>=0.2.2,<0.3.0',
            'wheel',
        ],
    },
    zip_safe=False,
)
