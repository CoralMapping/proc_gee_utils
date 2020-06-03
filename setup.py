from setuptools import find_packages, setup


with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name='eeutils',
    version='0.1.0',
    description='Utility functions for Google Earth Engine',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=['earthengine-api>=0.1.219'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache 2.0 Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    url='https://github.com/CoralMapping/proc_gee_utils'
)
