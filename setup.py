import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyodm",
    version="0.1.0",
    author="Piero Toffanin",
    author_email="pt@masseranolabs.com",
    description="Python SDK for OpenDroneMap",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenDroneMap/PyODM",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD-3-Clause",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'requests',
        'requests_toolbelt',
    ]
)