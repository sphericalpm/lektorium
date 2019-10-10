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
            'client/*/*/*'
        ]
    },
    install_requires=[
        'aiohttp-graphql',
        'aiohttp!=3.6.0',
        'appdirs',
        'beautifulsoup4',
        'bidict',
        'cached-property',
        'graphene',
        'graphql-core<3',
        'importlib-resources ; python_version < "3.7"',
        'lektor',
        'more-itertools',
        'nodeenv',
        'python-dateutil',
        'pyyaml',
    ],
    extras_require={
        'dev': [
            'aiohttp-devtools',
            'async-timeout',

            'mypy',
            'pydocstyle',
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'flake8',
            'flake8-import-order-spoqa',
            'flake8-docstrings',
            'flake8-builtins',
            'flake8-blind-except',
            'flake8-quotes',
            'flake8-eradicate',
            'flake8-print',
            'flake8-mutable',
            'flake8-spellcheck',
            'pep8-naming',
            'requests-mock',
            'wrapt',
        ]
    },
    zip_safe=True,
)
