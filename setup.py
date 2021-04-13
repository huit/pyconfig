import setuptools

requires = [
    'boto3==1.12.36',
    'botocore==1.15.36',
    'PyYAML==5.3.1',
    'pylog @ https://github.com/huit/pylog/archive/refs/tags/v0.0.2.tar.gz#egg=pylog',
]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyconfig",
    version="0.0.3",
    author="Michael Kerry",
    author_email="michael_kerry@harvard.edu",
    description="A package to facilitate use of config for aws-hosted python appilcations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/huit/pyconfig",
    project_urls={
        "Bug Tracker": "https://github.com/huit/pyconfig/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=requires,
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
)
