from django.template import TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as DjFSLoader
from django.template.loaders.app_directories import Loader as DjAppLoader

from haml.compiler import Compiler

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class FSLoader(DjFSLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        data, fn = super(FSLoader, self)\
        .load_template_source(template_name, template_dirs)

        if not template_name.endswith('.haml'):
            return data, fn

        out = StringIO()
        # TODO nasty open(fn) workaround .decode(settings.FILE_CHARSET) issue.
        # regex in compiler module stops matching... unsure why
        Compiler(open(fn), out).compile()

        return out.getvalue(), fn

    load_template_source.is_usable = True


class AppLoader(DjAppLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        data, fn = super(FSLoader, self)\
        .load_template_source(template_name, template_dirs)

        if not template_name.endswith('.haml'):
            return data, fn

        out = StringIO()
        # TODO nasty open(fn) workaround .decode(settings.FILE_CHARSET) issue.
        # regex in compiler module stops matching... unsure why
        Compiler(open(fn), out).compile()

        return out.getvalue(), fn

    load_template_source.is_usable = True
