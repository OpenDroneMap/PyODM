import doctest

if __name__ == "__main__":
    import pyodm
    doctest.testmod(pyodm)

    from pyodm import api
    doctest.testmod(api)