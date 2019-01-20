"""
API
======
"""

import requests
import mimetypes
import json
import os
from urllib.parse import urlunparse, urlencode, urlparse, parse_qs

import simplejson

from pyodm.types import NodeOption
from .exceptions import NodeConnectionError, TaskResponseError, NodeServerError
from .utils import MultipartEncoder
from requests_toolbelt.multipart import encoder


class Node:
    """A client to interact with NodeODM API.

        Args:
            host (str): Hostname or IP address of processing node
            port (int): Port of processing node
            token (str): token to use for authentication
            timeout (int): timeout value in seconds for network requests
    """

    def __init__(self, host, port, token="", timeout=30):
        self.host = host
        self.port = port
        self.token = token
        self.timeout = timeout

    @staticmethod
    def from_url(url, timeout=30):
        """Create a Node instance from a URL.

        Args:
            url (str): URL in the format proto://hostname:port/?token=value
            timeout (int): timeout value in seconds for network requests

        Returns:
            :func:`~Node`
        """
        u = urlparse(url)
        qs = parse_qs(url.query)

        port = u.port
        if port is None:
            port = 443 if u.scheme == 'https' else 80

        token = ""
        if 'token' in qs:
            token = qs['token'][0]

        return Node(u.hostname, port, token, timeout)

    def url(self, url, query={}):
        """Get a URL relative to this node.

        Args:
            url (str): relative URL
            query (dict): query values to append to the URL

        Returns:
            str: Absolute URL
        """
        netloc = self.host if (self.port == 80 or self.port == 443) else "{}:{}".format(self.host, self.port)
        proto = 'https' if self.port == 443 else 'http'

        if len(self.token) > 0:
            query['token'] = self.token

        return urlunparse((proto, netloc, url, '', urlencode(query), ''))

    def get(self, url, query={}):
        try:
            return requests.get(self.url(url, query), timeout=self.timeout).json()
        except (json.decoder.JSONDecodeError, simplejson.JSONDecodeError) as e:
            raise NodeServerError(str(e))
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NodeConnectionError(str(e))

    def info(self):
        """Retrieve information about this node.

        >>> n = Node('localhost', 3000)
        >>> n.info()['taskQueueCount']
        0
        >>> list(n.info())
        ['version', 'taskQueueCount', 'totalMemory', 'availableMemory', 'cpuCores', 'maxImages', 'maxParallelTasks', 'odmVersion']

        Returns:
            dict: Information about this node
        """
        return self.get('/info')

    def options(self):
        """Retrieve the options available for creating new tasks on this node.

        >>> n = Node('localhost', 3000)
        >>> n.options()[0].name
        'pc-classify'
        >>> n.options()[0].domain
        ['none', 'smrf', 'pmf']

        Returns:
            list: [:func:`~pyodm.types.NodeOption`]
        """
        return list(map(lambda o: NodeOption(**o), self.get('/options')))

    def create_task(self, files, name=None, options={}, upload_progress_callback=None):
        """Start processing a new task.
        At a minimum you need to pass a list of image paths. All other parameters are optional.

        Args:
            files (list): list of image paths + optional GCP file path.
            name (str): name for the task
            options (dict): options to use, for example {'orthophoto-resolution': 3, ...}
            upload_progress_callback (function): callback reporting upload progress (as a percentage)

        Returns:
            :func:`~Task`
        """

        options_list = [{'name': k, 'value': v} for k, v in options]

        fields = {
            'name': name,
            'options': json.dumps(options_list),
            'images': [(os.path.basename(f), read_file(f), (mimetypes.guess_type(f)[0] or "image/jpg")) for
                       f in files]
        }

        def create_callback(mpe):
            total_bytes = mpe.len

            def callback(monitor):
                if upload_progress_callback is not None and total_bytes > 0:
                    upload_progress_callback(monitor.bytes_read / total_bytes)

            return callback

        e = MultipartEncoder(fields=fields)
        m = encoder.MultipartEncoderMonitor(e, create_callback(e))

        try:
            result = requests.post(self.url("/task/new"),
                                 data=m,
                                 headers={'Content-Type': m.content_type}).json()
        except (json.decoder.JSONDecodeError, simplejson.JSONDecodeError) as e:
            raise NodeServerError(str(e))
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NodeConnectionError(e)

        if 'uuid' in result:
            return Task(self, result['uuid'])
        elif 'error' in result:
            raise TaskResponseError(result['error'])
        else:
            raise NodeServerError('Invalid response: ' + str(result))

class Task:
    """A task is created to process images. To create a task, use :func:`~Node.create_task`.

    Args:
        node (:func:`~Node`): node this task belongs to
        uuid (str): Unique identifier assigned to this task.
    """

    def __init__(self, node, uuid):
        self.node = node
        self.uuid = uuid


    def get(self, url, query = {}):
        result = self.node.get(url, query)
        if 'error' in result:
            raise TaskResponseError(result['error'])
        return result

    def info(self, uuid):
        return self.get('/task/{}/info'.format(uuid))

    def output(self, uuid, line=0):
        return self.get('/task/{}/output'.format(uuid), {'line': line})

    def task_cancel(self, uuid):
        return requests.post(self.url('/task/cancel'), data={'uuid': uuid}, timeout=self.timeout).json()

    def task_remove(self, uuid):
        return requests.post(self.url('/task/remove'), data={'uuid': uuid}, timeout=self.timeout).json()

    def task_restart(self, uuid, options=None):
        data = {'uuid': uuid}
        if options is not None: data['options'] = json.dumps(options)
        return requests.post(self.url('/task/restart'), data=data, timeout=self.timeout).json()

    def task_download(self, uuid, asset):
        res = requests.get(self.url('/task/{}/download/{}').format(uuid, asset), stream=True, timeout=self.timeout)
        if "Content-Type" in res.headers and "application/json" in res.headers['Content-Type']:
            return res.json()
        else:
            return res
