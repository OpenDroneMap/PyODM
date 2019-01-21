import sys
sys.path.append('..')

from pyodm import Node, exceptions

node = Node.from_url("http://localhost:3000")

try:
    task = node.create_task(files=['images/tiny_image_1.jpg', 'images/tiny_image_2.jpg'])
    print("Task UUID: %s" % task.uuid)

except exceptions.NodeConnectionError as e:
    print("Cannot connect: %s" % e)
except exceptions.TaskResponseError as e:
    print("Error: %s" % e)