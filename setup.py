import setuptools
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()

INSTALL_REQUIRES=[
    'requests==2.21.0',
    'requests_toolbelt==0.9.1',
    'urllib3==1.24.1',
]
if sys.version_info[0] < 3:
    INSTALL_REQUIRES.append("simplejson>=2.1.0")

setuptools.setup(
    name="pyodm",
    version="1.5.2b1",
    author="OpenDroneMap Contributors",
    author_email="pt@masseranolabs.com",
    description="Python SDK for OpenDroneMap",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenDroneMap/PyODM",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    install_requires=INSTALL_REQUIRES
)
