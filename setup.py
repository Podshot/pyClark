from setuptools import setup

import pyClark

setup(
    name='pyClark',
    url='https://github.com/Podshot/pyClark',
    version=pyClark.__version__,
    packages=['pyClark',],
    license='GNU LGPLv3',
    description='Remote error reporting that helps save the day',
    author='Podshot',
    author_email='ben.gothard3@gmail.com',
    install_requires=['requests'],
    data_files=[
        ('', ['LICENSE'])
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: System :: Monitoring',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='development'
)