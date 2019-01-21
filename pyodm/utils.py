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