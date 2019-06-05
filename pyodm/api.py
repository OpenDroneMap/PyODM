"""
API
======
"""
import zipfile
try:
    import queue
except ImportError:
    import Queue as queue
import threading
import datetime
import math

import requests
import mimetypes
import os
try:
    from urllib.parse import urlunparse, urlencode, urlparse, parse_qs
except ImportError:
    from urllib import urlencode
    from urlparse import urlunparse, urlparse, parse_qs

try:
    import simplejson as json
except ImportError:
    import json
import time

from urllib3.exceptions import ReadTimeoutError

from pyodm.types import NodeOption, NodeInfo, TaskInfo, TaskStatus
from pyodm.exceptions import NodeConnectionError, NodeResponseError, NodeServerError, TaskFailedError, OdmError, RangeNotAvailableError
from pyodm.utils import MultipartEncoder, options_to_json, AtomicCounter
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

        >>> n = Node.from_url("http://localhost:3000?token=abc")

        Args:
            url (str): URL in the format proto://hostname:port/?token=value
            timeout (int): timeout value in seconds for network requests

        Returns:
            :func:`~Node`
        """
        u = urlparse(url)
        qs = parse_qs(u.query)

        port = u.port
        if port is None:
            port = 443 if u.scheme == 'https' else 80

        token = ""
        if 'token' in qs:
            token = qs['token'][0]

        return Node(u.hostname, port, token, timeout)

    @staticmethod
    def compare_version(node_version, compare_version):
        # Compare two NodeODM versions
        # -1 = node version lower than compare
        # 0 = equal
        # 1 = node version higher than compare
        if node_version is None or len(node_version) < 3:
            return -1
        
        if node_version == compare_version:
            return 0

        try:
            (n_major, n_minor, n_build) = map(int, node_version.split("."))
            (c_major, c_minor, c_build) = map(int, compare_version.split("."))
        except:
            return -1

        n_number = 1000000 * n_major + 1000 * n_minor + n_build       
        c_number = 1000000 * c_major + 1000 * c_minor + c_build

        if n_number < c_number:
            return -1
        else:
            return 1

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

    def get(self, url, query={}, **kwargs):
        try:
            res = requests.get(self.url(url, query), timeout=self.timeout, **kwargs)
            if res.status_code == 401:
                raise NodeResponseError("Unauthorized. Do you need to set a token?")
            elif not res.status_code in [200, 403, 206]:
                raise NodeServerError("Unexpected status code: %s" % res.status_code)

            if "Content-Type" in res.headers and "application/json" in res.headers['Content-Type']:
                result = res.json()
                if 'error' in result:
                    raise NodeResponseError(result['error'])
                return result
            else:
                return res
        except json.decoder.JSONDecodeError as e:
            raise NodeServerError(str(e))
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NodeConnectionError(str(e))

    def post(self, url, data=None, headers={}):
        try:
            res = requests.post(self.url(url), data=data, headers=headers, timeout=self.timeout)

            if res.status_code == 401:
                raise NodeResponseError("Unauthorized. Do you need to set a token?")
            elif res.status_code != 200 and res.status_code != 403:
                raise NodeServerError(res.status_code)

            if "Content-Type" in res.headers and "application/json" in res.headers['Content-Type']:
                result = res.json()
                if 'error' in result:
                    raise NodeResponseError(result['error'])
                return result
            else:
                return res
        except json.decoder.JSONDecodeError as e:
            raise NodeServerError(str(e))
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise NodeConnectionError(str(e))


    def info(self):
        """Retrieve information about this node.

        >>> n = Node('localhost', 3000)
        >>> n.info().version
        '1.5.2'
        >>> n.info().engine
        'odm'

        Returns:
            :func:`~pyodm.types.NodeInfo`
        """
        return NodeInfo(self.get('/info'))

    def options(self):
        """Retrieve the options available for creating new tasks on this node.

        >>> n = Node('localhost', 3000)
        >>> n.options()[0].name
        'pc-classify'

        Returns:
            list: [:func:`~pyodm.types.NodeOption`]
        """
        return list(map(lambda o: NodeOption(**o), self.get('/options')))

    def version_greater_or_equal_than(self, version):
        """Checks whether this node version is greater than or equal than
        a certain version number.

        >>> n = Node('localhost', 3000)
        >>> n.version_greater_or_equal_than('1.3.1')
        True
        >>> n.version_greater_or_equal_than('10.5.1')
        False

        Args:
            version (str): version number to compare
        
        Returns:
            bool: result of comparison.
        """

        node_version = self.info().version
        return self.compare_version(node_version, version) >= 0


    def create_task(self, files, options={}, name=None, progress_callback=None, skip_post_processing=False, webhook=None, outputs=[], parallel_uploads=10, max_retries=5, retry_timeout=5):
        """Start processing a new task.
        At a minimum you need to pass a list of image paths. All other parameters are optional.

        >>> n = Node('localhost', 3000)
        >>> t = n.create_task(['examples/images/image_1.jpg', 'examples/images/image_2.jpg'], \
                          {'orthophoto-resolution': 2, 'dsm': True})
        >>> info = t.info()
        >>> info.status
        <TaskStatus.RUNNING: 20>
        >>> info.last_error
        ''
        >>> t.info().images_count
        2
        >>> t.output()[0:2]
        ['DJI_0131.JPG - DJI_0313.JPG has 1 candidate matches', 'DJI_0131.JPG - DJI_0177.JPG has 3 candidate matches']

        Args:
            files (list): list of image paths + optional GCP file path.
            options (dict): options to use, for example {'orthophoto-resolution': 3, ...}
            name (str): name for the task
            progress_callback (function): callback reporting upload progress percentage
            skip_post_processing  (bool): When true, skips generation of map tiles, derivate assets, point cloud tiles.
            webhook (str): Optional URL to call when processing has ended (either successfully or unsuccessfully).
            outputs (list): Optional paths relative to the project directory that should be included in the all.zip result file, overriding the default behavior.
            parallel_uploads (int): Number of parallel uploads.
            max_retries (int): Number of attempts to make before giving up on a file upload.
            retry_timeout (int): Wait at least these many seconds before attempting to upload a file a second time, multiplied by the retry number.
        Returns:
            :func:`~Task`
        """
        if not self.version_greater_or_equal_than("1.4.0"):
            return self.create_task_fallback(files, options, name, progress_callback)
        
        if len(files) == 0:
            raise NodeResponseError("Not enough images")

        fields = {
            'name': name,
            'options': options_to_json(options),
        }

        if skip_post_processing:
            fields['skipPostProcessing'] = 'true'
        
        if webhook is not None:
            fields['webhook'] = webhook

        if outputs:
            fields['outputs'] = json.dumps(outputs)

        e = MultipartEncoder(fields=fields)

        result = self.post('/task/new/init', data=e, headers={'Content-Type': e.content_type})
        if isinstance(result, dict) and 'error' in result:
            raise NodeResponseError(result['error'])
        
        if isinstance(result, dict) and 'uuid' in result:
            uuid = result['uuid']

            class nonloc:
                uploaded_files = AtomicCounter(0)
                error = None

            # Equivalent as passing the open file descriptor, since requests
            # eventually calls read(), but this way we make sure to close
            # the file prior to reading the next, so we don't run into open file OS limits
            def read_file(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()

            # Upload
            def worker():
                while True:
                    task = q.get()
                    if task is None or nonloc.error is not None:
                        q.task_done()
                        break
                    
                    # Upload file
                    if task['wait_until'] > datetime.datetime.now():
                        time.sleep((task['wait_until'] - datetime.datetime.now()).seconds)

                    try:
                        file = task['file']
                        fields = {
                            'images': [(os.path.basename(file), read_file(file), (mimetypes.guess_type(file)[0] or "image/jpg"))]
                        }

                        e = MultipartEncoder(fields=fields)
                        result = self.post('/task/new/upload/{}'.format(uuid), data=e, headers={'Content-Type': e.content_type})

                        if isinstance(result, dict) and 'success' in result and result['success']:
                            uf = nonloc.uploaded_files.increment()
                            if progress_callback is not None:
                                progress_callback(100.0 * uf / len(files))
                        else:
                            if isinstance(result, dict) and 'error' in result:
                                raise NodeResponseError(result['error'])
                            else:
                                raise NodeServerError("Failed upload with unexpected result: %s" % str(result))
                    except OdmError as e:
                        if task['retries'] < max_retries:
                            # Put task back in queue
                            task['retries'] += 1
                            task['wait_until'] = datetime.datetime.now() + datetime.timedelta(seconds=task['retries'] * retry_timeout)
                            q.put(task)
                        else:
                            nonloc.error = e
                    except Exception as e:
                        nonloc.error = e
                    finally:
                        q.task_done()


            q = queue.Queue()
            threads = []
            for i in range(parallel_uploads):
                t = threading.Thread(target=worker)
                t.start()
                threads.append(t)

            now = datetime.datetime.now()
            for file in files:
                q.put({
                    'file': file,
                    'wait_until': now,
                    'retries': 0
                })

            # block until all tasks are done
            q.join()

            # stop workers
            for i in range(parallel_uploads):
                q.put(None)
            for t in threads:
                t.join()

            if nonloc.error is not None:
                raise nonloc.error

            result = self.post('/task/new/commit/{}'.format(uuid))
            return self.handle_task_new_response(result)
        else:
            raise NodeServerError("Invalid response from /task/new/init: %s" % result)

    def create_task_fallback(self, files, options={}, name=None, progress_callback=None):
        # Pre chunked API create task implementation, used as fallback
        if len(files) == 0:
            raise NodeResponseError("Not enough images")

        # Equivalent as passing the open file descriptor, since requests
        # eventually calls read(), but this way we make sure to close
        # the file prior to reading the next, so we don't run into open file OS limits
        def read_file(file_path):
            with open(file_path, 'rb') as f:
                return f.read()

        fields = {
            'name': name,
            'options': options_to_json(options),
            'images': [(os.path.basename(f), read_file(f), (mimetypes.guess_type(f)[0] or "image/jpg")) for
                       f in files]
        }

        def create_callback(mpe):
            total_bytes = mpe.len

            def callback(monitor):
                if progress_callback is not None and total_bytes > 0:
                    progress_callback(100.0 * monitor.bytes_read / total_bytes)

            return callback

        e = MultipartEncoder(fields=fields)
        m = encoder.MultipartEncoderMonitor(e, create_callback(e))

        result = self.post('/task/new', data=m, headers={'Content-Type': m.content_type})

        return self.handle_task_new_response(result)

    def handle_task_new_response(self, result):
        if isinstance(result, dict) and 'uuid' in result:
            return Task(self, result['uuid'])
        elif isinstance(result, dict) and 'error' in result:
            raise NodeResponseError(result['error'])
        else:
            raise NodeServerError('Invalid response: ' + str(result))

    def get_task(self, uuid):
        """Helper method to initialize a task from an existing UUID

        >>> n = Node("localhost", 3000)
        >>> t = n.get_task('00000000-0000-0000-0000-000000000000')
        >>> t.__class__
        <class 'pyodm.api.Task'>

        Args:
            uuid: Unique identifier of the task
        """
        return Task(self, uuid)

class Task:
    """A task is created to process images. To create a task, use :func:`~Node.create_task`.

    Args:
        node (:func:`~Node`): node this task belongs to
        uuid (str): Unique identifier assigned to this task.
    """

    def __init__(self, node, uuid):
        self.node = node
        self.uuid = uuid


    def get(self, url, query = {}, **kwargs):
        result = self.node.get(url, query, **kwargs)
        if isinstance(result, dict) and 'error' in result:
            raise NodeResponseError(result['error'])
        return result

    def post(self, url, data):
        result = self.node.post(url, data)
        if isinstance(result, dict) and 'error' in result:
            raise NodeResponseError(result['error'])
        return result

    def info(self, with_output=None):
        """Retrieves information about this task.

        Returns:
            :func:`~pyodm.types.TaskInfo`
        """
        query = {}
        if with_output is not None:
            query['with_output'] = with_output

        return TaskInfo(self.get('/task/{}/info'.format(self.uuid), query))

    def output(self, line=0):
        """Retrieve console task output.

        Args:
            line (int): Optional line number that the console output should be truncated from. For example, passing a value of 100 will retrieve the console output starting from line 100. Negative numbers are also allowed. For example -50 will retrieve the last 50 lines of console output. Defaults to 0 (retrieve all console output).

        Returns:
            [str]: console output (one list item per row).
        """
        return self.get('/task/{}/output'.format(self.uuid), {'line': line})

    def cancel(self):
        """Cancel this task.

        Returns:
            bool: task was canceled or not
        """
        return self.post('/task/cancel', {'uuid': self.uuid}).get('success', False)

    def remove(self):
        """Remove this task.

        Returns:
            bool: task was removed or not
        """
        return self.post('/task/remove', {'uuid': self.uuid}).get('success', False)

    def restart(self, options=None):
        """Restart this task.

        Args:
            options (dict): options to use, for example {'orthophoto-resolution': 3, ...}

        Returns:
            bool: task was restarted or not
        """
        data = {'uuid': self.uuid}
        if options is not None: data['options'] = options_to_json(options)
        return self.post('/task/restart', data).get('success', False)

    def download_zip(self, destination, progress_callback=None, parallel_downloads=16, parallel_chunks_size=10):
        """Download this task's assets archive to a directory.

        Args:
            destination (str): directory where to download assets archive. If the directory does not exist, it will be created.
            progress_callback (function): an optional callback with one parameter, the download progress percentage.
            parallel_downloads (int): maximum number of parallel downloads if the node supports http range.
            parallel_chunks_size (int): size in MB of chunks for parallel downloads
        Returns:
            str: path to archive file (.zip)
        """
        info = self.info()
        if info.status != TaskStatus.COMPLETED:
            raise NodeResponseError("Cannot download task, task status is " + str(info.status))

        if not os.path.exists(destination):
            os.makedirs(destination, exist_ok=True)

        try:
            download_stream = self.get('/task/{}/download/all.zip'.format(self.uuid), stream=True)
            headers = download_stream.headers
            
            zip_path = os.path.join(destination, "{}_{}_all.zip".format(self.uuid, int(time.time())))

            # Keep track of download progress (if possible)
            content_length = download_stream.headers.get('content-length')
            total_length = int(content_length) if content_length is not None else None
            downloaded = 0
            chunk_size = int(parallel_chunks_size * 1024 * 1024)
            use_fallback = False
            accept_ranges = headers.get('accept-ranges')

            # Can we do parallel downloads?
            if accept_ranges is not None and accept_ranges.lower() == 'bytes' and total_length is not None and total_length > chunk_size and parallel_downloads > 1:
                num_chunks = int(math.ceil(total_length / float(chunk_size)))
                num_workers = parallel_downloads

                class nonloc:
                    completed_chunks = AtomicCounter(0)
                    merge_chunks = [False] * num_chunks
                    error = None

                def merge():
                    current_chunk = 0

                    with open(zip_path, "wb") as out_file:
                        while current_chunk < num_chunks and nonloc.error is None:
                            if nonloc.merge_chunks[current_chunk]:
                                chunk_file = "%s.part%s" % (zip_path, current_chunk)
                                with open(chunk_file, "rb") as fd:
                                    out_file.write(fd.read())

                                os.unlink(chunk_file)
                                
                                current_chunk += 1
                            else:
                                time.sleep(0.1)

                def worker():
                    while True:
                        task = q.get()
                        part_num, bytes_range = task
                        if bytes_range is None or nonloc.error is not None:
                            q.task_done()
                            break

                        try:
                            # Download chunk
                            res = self.get('/task/{}/download/all.zip'.format(self.uuid), stream=True, headers={'Range': 'bytes=%s-%s' % bytes_range})
                            if res.status_code == 206:
                                with open("%s.part%s" % (zip_path, part_num), 'wb') as fd:
                                    for chunk in res.iter_content(4096):
                                        fd.write(chunk)
                                    
                                with nonloc.completed_chunks.lock:
                                    nonloc.completed_chunks.value += 1

                                    if progress_callback is not None:
                                        progress_callback(100.0 * nonloc.completed_chunks.value / num_chunks)
                            
                                nonloc.merge_chunks[part_num] = True
                            else:
                                nonloc.error = RangeNotAvailableError()
                        except OdmError as e:
                            time.sleep(5)
                            q.put((part_num, bytes_range))
                        except Exception as e:
                            nonloc.error = e
                        finally:
                            q.task_done()

                q = queue.PriorityQueue()
                threads = []
                for i in range(num_workers):
                    t = threading.Thread(target=worker)
                    t.start()
                    threads.append(t)

                merge_thread = threading.Thread(target=merge)
                merge_thread.start()

                range_start = 0

                for i in range(num_chunks):
                    range_end = min(range_start + chunk_size - 1, total_length - 1)
                    q.put((i, (range_start, range_end)))
                    range_start = range_end + 1

                # block until all tasks are done
                q.join()

                # stop workers
                for i in range(len(threads)):
                    q.put((-1, None))
                for t in threads:
                    t.join()
                
                merge_thread.join()

                if nonloc.error is not None:
                    if isinstance(nonloc.error, RangeNotAvailableError):
                        use_fallback = True
                    else:
                        raise nonloc.error
            else:
                use_fallback = True

            if use_fallback:
                # Single connection, boring download
                with open(zip_path, 'wb') as fd:
                    for chunk in download_stream.iter_content(4096):
                        downloaded += len(chunk)

                        if progress_callback is not None and total_length is not None:
                            progress_callback((100.0 * float(downloaded) / total_length))

                        fd.write(chunk)
                    
                    if progress_callback is not None:
                        progress_callback(100)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, ReadTimeoutError) as e:
            raise NodeConnectionError(e)

        return zip_path

    def download_assets(self, destination, progress_callback=None, parallel_downloads=16, parallel_chunks_size=10):
        """Download this task's assets to a directory.

        Args:
            destination (str): directory where to download assets. If the directory does not exist, it will be created.
            progress_callback (function): an optional callback with one parameter, the download progress percentage
            parallel_downloads (int): maximum number of parallel downloads if the node supports http range.
            parallel_chunks_size (int): size in MB of chunks for parallel downloads
        Returns:
            str: path to saved assets
        """
        zip_path = self.download_zip(destination, progress_callback=progress_callback, parallel_downloads=parallel_downloads, parallel_chunks_size=parallel_chunks_size)
        with zipfile.ZipFile(zip_path, "r") as zip_h:
            zip_h.extractall(destination)
            os.remove(zip_path)

        return destination

    def wait_for_completion(self, status_callback=None, interval=3, max_retries=5, retry_timeout=5):
        """Wait for the task to complete. The call will block until the task status has become
        :func:`~TaskStatus.COMPLETED`. If the status is set to :func:`~TaskStatus.CANCELED` or :func:`~TaskStatus.FAILED`
        it raises a TaskFailedError exception.

        Args:
            status_callback (function): optional callback that will be called with task info updates every interval seconds.
            interval (int): seconds between status checks.
            max_retries (int): number of repeated attempts that should be made to receive a status update before giving up.
            retry_timeout (int): wait N*retry_timeout between attempts, where N is the attempt number.
        """
        retry = 0

        while True:
            try:
                info = self.info()
            except NodeConnectionError as e:
                if retry < max_retries:
                    retry += 1
                    time.sleep(retry * retry_timeout)
                    continue
                else:
                    raise e

            retry = 0
            if status_callback is not None:
                status_callback(info)

            if info.status in [TaskStatus.COMPLETED, TaskStatus.CANCELED, TaskStatus.FAILED]:
                break

            time.sleep(interval)

        if info.status in [TaskStatus.FAILED, TaskStatus.CANCELED]:
            raise TaskFailedError(info.status)
