import sys
sys.path.append('..')

from pyodm import Node, exceptions

node = Node.from_url("http://localhost:3000?token=abc")

try:
    print(node.info())
except exceptions.NodeConnectionError as e:
    print("Cannot connect: " + str(e))