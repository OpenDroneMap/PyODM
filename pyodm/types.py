from datetime import datetime

class NodeInfo:
    """Information about a node
    
    Args:
        version (str): Current API version
        task_queue_count (int): Number of tasks currently being processed or waiting to be processed
        total_memory (int): Amount of total RAM in the system in bytes
        available_memory (int): Amount of RAM available in bytes
        cpu_cores (int): Number of virtual CPU cores
        max_images (int): Maximum number of images allowed for new tasks or null if there’s no limit.
        max_parallel_tasks (int): Maximum number of tasks that can be processed simultaneously
        odm_version (str): Current version of ODM
    """
    def __init__(self, json):
        self.version = json['version']
        self.task_queue_count = json['taskQueueCount']
        self.total_memory = json['totalMemory']
        self.available_memory = json['availableMemory']
        self.cpu_cores = json['cpuCores']
        self.max_images = json['maxImages']
        self.max_parallel_tasks = json['maxParallelTasks']
        self.odm_version = json['odmVersion']


class NodeOption:
    """A node option available to be passed to a node.

    Args:
        domain (str): Valid range of values
        help (str): Description of what this option does
        name (str): Option name
        value (str): Default value for this option
        type (str): One of: ['int', 'float', 'string', 'bool', 'enum']
    """
    def __init__(self, domain, help, name, value, type):
        self.domain = domain
        self.help = help
        self.name = name
        self.value = value
        self.type = type


class TaskInfo:
    """Task information

    Args:
        uuid (str): Unique identifier
        name (str): Human friendly name
        date_created (datetime): Creation date and time
        processing_time (int): Milliseconds that have elapsed since the start of processing, or -1 if no information is available.
        status (:func:`pyodm.types.TaskStatus`): status (running, queued, etc.)
        options (dict): options used for this task
        imagesCount (int): Number of images (+ GCP file)
    """
    def __init__(self, json):
        self.uuid = json['uuid']
        self.name = json['name']
        self.date_created = datetime.utcfromtimestamp(int(json['dateCreated'] / 1000.0))
        self.processing_time = json['processingTime']
        self.status = TaskStatus(json['status']['code'])
        self.options = json['options']
        self.images_count = json['imagesCount']


from enum import Enum
class TaskStatus(Enum):
    """Task status

    Args:
        QUEUED: Task’s files have been uploaded and are waiting to be processed.
        RUNNING: Task is currently being processed.
        FAILED:	Task has failed for some reason (not enough images, out of memory, etc.
        COMPLETED: Task has completed. Assets are be ready to be downloaded.
        CANCELED: Task was manually canceled by the user.
    """
    QUEUED = 10
    RUNNING = 20
    FAILED = 30
    COMPLETED = 40
    CANCELED = 50

