from distutils.core import setup

import pyClark

setup(
    name='pyClark',
    version=pyClark.__version__,
    packages=['pyClark',],
    license='GNU LGPLv3',
    description='Remote error reporting that helps save the day',
    author='Podshot',
    install_requires=['requests'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: System :: Monitoring'
    ],
    keywords='development'
)