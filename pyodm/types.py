from datetime import datetime

class JsonResponse:
    def __str__(self):
        return str({key: value for key, value in self.__dict__.items() if not key.startswith("__")})

class NodeInfo(JsonResponse):
    """Information about a node
    
    Args:
        version (str): Current API version
        task_queue_count (int): Number of tasks currently being processed or waiting to be processed
        total_memory (int): Amount of total RAM in the system in bytes
        available_memory (int): Amount of RAM available in bytes
        cpu_cores (int): Number of virtual CPU cores
        max_images (int): Maximum number of images allowed for new tasks or None if there's no limit.
        max_parallel_tasks (int): Maximum number of tasks that can be processed simultaneously
        odm_version (str): Current version of ODM (deprecated, use engine_version instead)
        engine (str): Lowercase identifier of the engine (odm, micmac, ...)
        engine_version (str): Current engine version
    """
    def __init__(self, json):
        self.version = json.get('version', '?')
        self.task_queue_count = json.get('taskQueueCount')
        self.total_memory = json.get('totalMemory')
        self.available_memory = json.get('availableMemory')
        self.cpu_cores = json.get('cpuCores')
        self.max_images = json.get('maxImages')
        self.max_parallel_tasks = json.get('maxParallelTasks')
        self.engine = json.get('engine', '?')
        self.engine_version = json.get('engineVersion', '?')
        
        # Deprecated
        self.odm_version = json.get('odmVersion', '?')

        # Guess
        if self.engine_version == '?' and self.odm_version != '?':
            self.engine = 'odm'
            self.engine_version = self.odm_version


class NodeOption(JsonResponse):
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


class TaskInfo(JsonResponse):
    """Task information

    Args:
        uuid (str): Unique identifier
        name (str): Human friendly name
        date_created (datetime): Creation date and time
        processing_time (int): Milliseconds that have elapsed since the start of processing, or -1 if no information is available.
        status (:func:`pyodm.types.TaskStatus`): status (running, queued, etc.)
        last_error (str): if the task fails, this will be set to a string representing the last error that occured, otherwise it's an empty string.
        options (dict): options used for this task
        images_count (int): Number of images (+ GCP file)
        progress (float): Percentage progress (estimated) of the task
        output ([str]): Optional console output (one list item per row). This is populated only if the with_output parameter is passed to info().
    """
    def __init__(self, json):
        self.uuid = json['uuid']
        self.name = json['name']
        self.date_created = datetime.utcfromtimestamp(int(json['dateCreated'] / 1000.0))
        self.processing_time = json['processingTime']
        self.status = TaskStatus(json['status']['code'])
        self.last_error = json['status'].get('errorMessage', '')
        self.options = json['options']
        self.images_count = json['imagesCount']
        self.progress = json.get('progress', 0)
        self.output = json.get('output', [])


from enum import Enum
class TaskStatus(Enum):
    """Task status

    Args:
        QUEUED: Task's files have been uploaded and are waiting to be processed.
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

