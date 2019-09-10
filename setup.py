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
    ],
    package_dir={
        '': 'src',
    },
    install_requires=[
        'aiohttp',
        'aiohttp-graphql',
        'graphene',
        'nodeenv',
        'graphql-core<3',
        'pyyaml',
    ],
    extras_require={
        'dev': [
            'aiohttp-devtools',
        ]
    },
    zip_safe=True,
)
