# PyODM

For documentation, please visit 

## Running Tests

```
python run_tests.py
```

Will run the all doctests. You must have a NodeODM node running in test mode locally to run the test suite:

```bash
docker run -ti -p 3000:3000 opendronemap/nodeodm --test
``` 

## Building The Documentation

Make sure you are using Python 3.

```bash
pip install virtualenv
virtualenv -p venv
source venv/bin/activate
pip install -r requirements.txt
```

Use [`sphinx-autobuild`](https://github.com/GaretJax/sphinx-autobuild) to automatically watch for changes and rebuild the html site using:

```
cd docs
make livehtml
```

To stop the server press `Ctrl+C`.

## Publishing to PyPI

```bash
pip install setuptools wheel twine
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```

See https://packaging.python.org/tutorials/packaging-projects/ for more information.

## Support the Project

There are many ways to contribute to the project:

 - ⭐️ us on GitHub.
 - Help us test the application.
 - Spread the word about OpenDroneMap on social media.
 - Help answer questions on the community [forum](https://community.opendronemap.org)
 - Become a contributor!




