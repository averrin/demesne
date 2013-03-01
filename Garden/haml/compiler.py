from haml import util

import regex

class Node(object):
    autoclose_tags = [
        'meta',
        'img',
        'link',
        'br',
        'hr',
        'input',
        'area',
        'param',
        'col',
        'base'
    ]
    kinds = (
        'element',
        'doctype',
        'html_cond_comment',
        'html_comment',
        'comment',
        'plain',
        'variable',
        'tag',
        )
    tags_to_close = (
        'autoescape',
        'block',
        'comment',
        'filter',
        'for',
        'if',
        'ifchanged',
        'ifequal',
        'ifnotequal',
        'spaceless',
        'with',
        )

    def __init__(self, content, match):
        self.children = []
        self.content = content
        self.match = match
        self.plain = self.match['plain']

    def __iadd__(self, other):
        # XXX only makes sense at the moment for plain nodes
        self.plain += '\n' + other.match['indent'] + other.plain
        return self

    def build_attrs(self, kvs):
        attrs = {}
        for key, value in kvs:
            v = ''
            for part in value.split('+'):
                part = part.strip()
                if part.startswith('"'):
                    if not part.endswith('"'):
                        raise self.ParseError(
                            'part missing ending double quote: %s' % part
                        )
                    v += part[1:-1]
                elif part.startswith("'"):
                    if not part.endswith("'"):
                        raise self.ParseError(
                            'part missing ending single quote: %s' % part
                        )
                    v += part[1:-1]
                else:
                    v += self.template_variable(part)
            attrs[key] = v
        return attrs

    def closed(self):
        try:
            return getattr(self, 'closed_%s' % self.kind)()
        except AttributeError:
            return True

    def closed_element(self):
        tag, ids, classes, attrs, close, has_content = self._render_element()
        if has_content:
            return True
        return close

    def closed_html_comment(self):
        return bool(self.match['html_comment'][1:])

    def closed_html_cond_comment(self):
        return False

    def closed_tag(self):
        return not self.tag_name() in self.tags_to_close

    def iter_children(self):
        assert self.children # required

        kwargs = util.DictAttr()
        kwargs.prev = self
        kwargs.prev_sibling = False
        curr = None
        for child in self.children:
            if curr is not None:
                if curr.kind == 'plain' and child.kind == 'plain':
                    curr += child
                    continue

                else:
                    kwargs.next = child
                    kwargs.next_sibling = True
                    yield curr, kwargs
                    kwargs.prev = curr
                    kwargs.prev_sibling = True
            curr = child

        kwargs.next = self
        kwargs.next_sibling = False
        yield curr, kwargs

    @property
    def kind(self):
        for name in self.kinds:
            if self.match[name]:
                return name
        return ''

    def parse_elements(self, elements):
        tag = None
        ids = []
        classes = []
        for el in elements:
            if el.startswith('%'):
                if tag is not None:
                    raise self.ParseError('multiple tags specified')
                tag = el[1:]

            elif el.startswith('.'):
                classes.append(el[1:])

            elif el.startswith('#'):
                ids.append(el[1:])

            else:
                raise self.ParseError('unknown element type: %s' % el)
        return tag, ids, classes

    def render(self, stream,
               prev=None, prev_sibling=False,
               next=None, next_sibling=False):
        content_or_f = getattr(self, 'render_%s' % self.kind, self.content)
        if callable(content_or_f):
            indent = self.match['indent']
            starttag, content, endtag = content_or_f()
            if not (prev and not prev_sibling and prev.match['consume_within'])\
               and not self.match['consume_around']\
            and not (prev and prev.match['consume_around']):
                stream.write(indent)
            if starttag:
                stream.write(starttag)
                if content:
                    stream.write(content)

                if endtag:
                    if self.children:
                        if not self.match['consume_within']:
                            stream.write('\n')

                        for child, kwargs in self.iter_children():
                            child.render(stream, **kwargs)

                        if not self.match['consume_within']:
                            if not (next and not next_sibling and next.match['consume_within']):
                                stream.write(indent)
                            else:
                                stream.write(next.match['indent'])

                    stream.write(endtag)
                    if not (next and not next_sibling and next.match['consume_within'])\
                    and not self.match['consume_around']:
                        stream.write('\n')

                else:
                    if not (next and next.match['consume_around'])\
                    and not self.match['consume_around']:
                        stream.write('\n')

            elif content:
                stream.write(content)
                if not (prev and not prev_sibling and prev.match['consume_within']):
                    stream.write('\n')
        else:
            stream.write(content_or_f)
            stream.write('\n')

    def render_comment(self):
        return '', '', ''

    def render_doctype(self):
        return '<!DOCTYPE %s>' % self.match['doctype'][1:], '', ''

    def _render_element(self):
        keys = []
        values = []
        keys.extend(self.match.captures('key'))
        keys.extend(self.match.captures('key2'))
        values.extend(self.match.captures('value'))
        values.extend(self.match.captures('value2'))

        tag, ids, classes = self.parse_elements(self.match.captures('element'))
        attrs = self.build_attrs(zip(keys, values))

        if tag is None:
            tag = 'div'

        close = self.match['close'] or tag.lower() in self.autoclose_tags

        return tag, ids, classes, attrs, close, bool(self.match['content'])

    def render_element(self):
        tag, ids, classes, attrs, close, has_content = self._render_element()

        if 'id' in attrs:
            ids.append(attrs.pop('id'))
        if 'class' in attrs:
            classes.append(attrs.pop('class'))

        starttag = '<%s' % tag
        if ids:
            starttag += ' id="%s"' % '_'.join(ids)
        if classes:
            starttag += ' class="%s"' % ' '.join(classes)
        for key, value in sorted(attrs.items(), key=lambda x: x[0]):
            starttag += ' %s="%s"' % (key, value)

        if close:
            starttag += ' /'
        starttag += '>'

        content = ''
        endtag = ''
        if self.match['content']:
            if self.match['var']:
                content += self.template_variable(self.match['content'][1:])
            else:
                content += self.match['content'][1:]

            if not close:
                endtag = '</%s>' % tag

        elif not close:
            endtag = '</%s>' % tag

        return starttag, content, endtag

    def render_html_comment(self):
        return '<!-- ', self.match['html_comment'][1:], ' -->'

    def render_html_cond_comment(self):
        return '<!--%s>' % self.match['html_cond_comment'][1:],\
               '',\
               '<![endif]-->'

    def render_plain(self):
        return '', self.plain, ''

    def render_variable(self):
        return '', self.template_variable(self.match['variable'][2:]), ''

    def render_tag(self):
        start, end = self.template_tag(
            self.tag_name(),
            self.match['tag'][2:]
        )
        return start, '', end

    def tag_name(self):
        return self.match['tag'].split(' ')[1]

    def template_variable(self, name):
        return '{{ %s }}' % name

    def template_tag(self, name, content):
        start = '{%% %s %%}' % content
        end = ''
        if name in self.tags_to_close:
            end = '{%% end%s %%}' % name
        return start, end


class Compiler(object):
    class ParseError(Exception): pass

    re_indent = regex.compile(r'^(?<indent>\s*)')
    re_haml = regex.compile(r'''
        ^(?<indent>\s*)
        (?:
            (?<element>[%.#][a-zA-Z0-9_-]+)+
            (?:{\s*
                (?:(?<key>[a-zA-Z][a-zA-Z0-9_-]*)
                   \s*=\s*
                   (?<value>[^,]+)

                   (?:\s*,\s*
                      (?<key2>[a-zA-Z][a-zA-Z0-9_-]*)
                      \s*=\s*
                      (?<value2>[^,]+)
                   )*
                )?
               \s*}
            )?
            (?<consume_around>>)?
            (?<consume_within><)?
            (?:(?<close>/)|(?<var>=)?(?<content> .*)?)
        |   (?<filter>:[a-zA-Z][a-zA-Z0-9_-]*)
        |   (?<doctype>!.*)
        |   (?<html_cond_comment>/\[.*\])
        |   (?<html_comment>/.*)
        |   (?<comment>-\#.*)
        |   (?<variable>= .*)
        |   (?<tag>- .*)
        |   \\?(?<plain>.*)
        )
    ''', regex.VERBOSE)

    def __init__(self, stream, outstream, nodeklass=None):
        if nodeklass is None:
            nodeklass = Node

        self.nodeklass = nodeklass

        self.stream = stream
        self.outstream = outstream

        self.__iter = None
        self.__redo_last = False

    def compile(self):
        rootnode = self.nodeklass('', self.re_haml.match(''))
        rootnode.children = self._compile()
        for child, kwargs in rootnode.iter_children():
            child.render(self.outstream, **kwargs)

    def _compile(self, level=-1, parent=None):
        nodes = []
        for last, curr, next in self.parse_iter():
            indent = curr.m['indent']
            empty = len(indent) == len(curr.line_stripped)
            if len(indent) <= level and not empty:
                # return if indent changed (and not due to an empty line)
                self.parse_iter_redo_last()
                return nodes

            if curr.m['filter']:
                node = self.nodeklass(
                    self.filter(curr.m['filter'][1:], indent),
                    curr.m
                )

            elif empty:
                node = self.nodeklass(curr.line_stripped, curr.m)

            else:
                node = self.nodeklass('', curr.m)
                if not node.closed():
                    node.children = self._compile(level=len(indent))
            nodes.append(node)

        return nodes

    def filter(self, name, indent):
        f = getattr(self, 'filter_%s' % name)
        content = ''
        for last, curr, next in self.parse_iter():
            if len(curr.m['indent']) <= len(indent):
                self.parse_iter_redo_last()
                break
            content += curr.line
        return f(indent, content)

    def filter_css(self, indent, content):
        return '%s<style type="text/css">\n%s\n%s</style>\n' % (
            indent, content, indent
            )

    def filter_plain(self, indent, content):
        return content

    def filter_javascript(self, indent, content):
        return '%s<script type="text/javascript">\n%s\n%s</script>\n' % (
            indent, content, indent
            )

    def _parse_iter(self):
        self.__redo_last = False
        last = util.DictAttr()

        curr = util.DictAttr()
        curr.line = self.stream.readline()
        curr.line_stripped = curr.line.rstrip('\r\n')
        curr.m = self.re_haml.match(curr.line)

        count = 0
        while curr.line:
            if self.__redo_last:
                self.__redo_last = False

            else:
                next = util.DictAttr()
                next.line = self.stream.readline()
                next.line_stripped = next.line.rstrip('\r\n')
                next.m = self.re_haml.match(next.line_stripped)

            count += 1
            if count > 100:
                break
            yield last, curr, next

            if not self.__redo_last:
                last = curr
                curr = next

        next = util.DictAttr()

        yield last, curr, next

        self.__iter = None

    def parse_iter(self):
        if self.__iter is None:
            self.__iter = self._parse_iter()
        return self.__iter

    def parse_iter_redo_last(self):
        self.__redo_last = True

if '__main__' == __name__:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

    stream = StringIO('''
!html
- load util
%html
    %head
        %title title of the page
        %link{rel='stylesheet', type='text/css', src='static/css/base.css'}
        %link{rel='stylesheet', type='text/css', src=STATIC_URL + 'css/base.css'}/
        /[if IE]
            %link{rel='stylesheet', type='text/css', src=STATIC_URL + 'css/ie.css'}/
    %body
        /html comment
        #header header
        %p hello world
        -# comment
        %p second paragraph
        %p.footnote
        %blockquote<
            %div
                Foo!
        %img

        %img
        %img>
        %img

        %p<= "Foo\\nBar"

        %img
        %pre><
            foo
            bar
        %img

        - if True
            %p
                = ONE
                = TWO
                = THREE
        %ul
            %li= one
            %li= two
            %li= three
        /
            %div inside
            %div multi
            %div line
            %div comment
        /
            text inside
            multi
            line
            comment
        %p
            text inside of a
            paragraph block tag
            \:javascript
        %p
            <div class="hmm">inline html</div>
        #footer footer
        :javascript
            $(function() {
                alert("hello world!");
            });
            // hello
        %script{type='text/javascript'}
            var a = 1;
            // hello
'''.lstrip())
    import sys

    Compiler(stream, sys.stdout).compile()
