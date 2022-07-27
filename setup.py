import setuptools
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()

INSTALL_REQUIRES=[
    'requests',
    'requests_toolbelt',
    'urllib3',
]
if sys.version_info[0] < 3:
    INSTALL_REQUIRES.append("simplejson>=2.1.0")

setuptools.setup(
    name="pyodm",
    version="1.5.10",
    author="OpenDroneMap Contributors",
    author_email="pt@uav4geo.com",
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
