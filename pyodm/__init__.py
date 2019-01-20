"""
PyODM is a library for easily creating orthophotos, DEMs, 3D models and point clouds from images aerial images via the `NodeODM API`_.


Simple usage:
   >>> from pyodm import Node
   >>> # TODO MORE EXAMPLE
   >>> print("HELLO")
   HELLO

License: BSD 3-Clause, see LICENSE for more details.

.. _NodeODM API:
   https://github.com/OpenDroneMap/NodeODM/blob/master/docs/index.adoc
"""

name = "pyodm"
from .api import Node, Task