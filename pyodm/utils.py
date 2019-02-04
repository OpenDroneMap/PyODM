import json, os, threading

from requests_toolbelt.multipart import encoder
from requests.packages.urllib3.fields import RequestField

# Extends class to support multipart form data
# fields with the same name
# https://github.com/requests/toolbelt/issues/225
class MultipartEncoder(encoder.MultipartEncoder):
    """Multiple files with the same name support, i.e. files[]"""

    def _iter_fields(self):
        _fields = self.fields
        if hasattr(self.fields, 'items'):
            _fields = list(self.fields.items())
        for k, v in _fields:
            for field in self._iter_field(k, v):
                yield field

    @classmethod
    def _iter_field(cls, field_name, field):
        file_name = None
        file_type = None
        file_headers = None
        if field and isinstance(field, (list, tuple)):
            if all([isinstance(f, (list, tuple)) for f in field]):
                for f in field:
                    yield next(cls._iter_field(field_name, f))
                else:
                    return

            if len(field) == 2:
                file_name, file_pointer = field
            elif len(field) == 3:
                file_name, file_pointer, file_type = field
            else:
                file_name, file_pointer, file_type, file_headers = field
        else:
            file_pointer = field

        field = RequestField(name=field_name,
                             data=file_pointer,
                             filename=file_name,
                             headers=file_headers)
        field.make_multipart(content_type=file_type)
        yield field


def options_to_json(options):
    """Convert a dictionary of options {k1: v1, k2: v2, ...} to a JSON
    string suitable for passing as an argument to the NodeODM API.

    Args:
        options: options for example {'orthophoto-resolution': 3, ...}

    Returns:
        str: JSON options
    """
    return json.dumps([{'name': k, 'value': options[k]} for k in options])



class AtomicCounter:
    """Atomic, thread-safe counter."""

    def __init__(self, val=0):
        """Initialize a new atomic counter to given initial value (default 0)."""
        self.value = val
        self.lock = threading.Lock()

    def increment(self, val=1):
        """Atomically increment the counter return the new value."""
        with self.lock:
            self.value += val
            return self.value
