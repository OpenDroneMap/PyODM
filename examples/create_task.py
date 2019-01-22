import os
import sys
sys.path.append('..')

from pyodm import Node, exceptions

node = Node("localhost", 3000)

try:
    # Start a task
    print("Uploading images...")
    task = node.create_task(['images/image_1.jpg', 'images/image_2.jpg'],
                            {'dsm': True, 'orthophoto-resolution': 4})
    print(task.info())

    try:
        # This will block until the task is finished
        # or will raise an exception
        task.wait_for_completion()

        print("Task completed, downloading results...")

        # Retrieve results
        task.download_assets("./results")

        print("Assets saved in ./results (%s)" % os.listdir("./results"))

        # Restart task and this time compute dtm
        task.restart({'dtm': True})
        task.wait_for_completion()

        print("Task completed, downloading results...")

        task.download_assets("./results_with_dtm")

        print("Assets saved in ./results_with_dtm (%s)" % os.listdir("./results_with_dtm"))
    except exceptions.TaskFailedError as e:
        print("\n".join(task.output()))

except exceptions.NodeConnectionError as e:
    print("Cannot connect: %s" % e)
except exceptions.NodeResponseError as e:
    print("Error: %s" % e)
