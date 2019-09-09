import setuptools


setuptools.setup(
    name='lektorium',

    use_scm_version=dict(
        root='../..'
    ),
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
        'flask',
        'nodeenv',
        'flask-graphql',
        'graphene',
        'pyyaml',
    ],
    zip_safe=True,
)
