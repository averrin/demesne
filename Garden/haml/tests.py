try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import regex
import unittest

from haml import compiler

class TestRendering(unittest.TestCase):
    re_newline = regex.compile(r'\n')

    cases = (
        ('!html\n', '<!DOCTYPE html>\n\n'),
        ('%html\n', '<html>\n\n</html>\n'),
        ("%link.class{rel='stylesheet', type='text/css', src=STATIC_URL + 'css/ie.css'}",
         '<link class="class" rel="stylesheet" src="{{ STATIC_URL }}css/ie.css" type="text/css" />\n\n'
            ),
        ('''
        /[if IE]
            %link{rel='stylesheet', type='text/css', src=STATIC_URL + 'css/ie.css'}
        '''.strip(),
         '''<!--[if IE]>
                     <link rel="stylesheet" src="{{ STATIC_URL }}css/ie.css" type="text/css" />

         <![endif]-->
         '''
            ),
        ('/html comment', '<!-- html comment -->\n\n'),
        ('-# comment', '\n'),
        ('''
/
    multi
    line
    comment
'''.lstrip(), '''
<!-- 
    multi
    line
    comment

 -->
'''.lstrip()),
        ('%title title of the page', '<title>title of the page</title>\n\n'),
        ('#header header', '<div id="header">header</div>\n\n'),
        ('.myclass a class', '<div class="myclass">a class</div>\n\n'),
        ('%p.footnote a footnote', '<p class="footnote">a footnote</p>\n\n'),
        ('%p= VARIABLE', '<p>{{ VARIABLE }}</p>\n\n'),
        ('%selfclose/', '<selfclose />\n\n'),
        ('\%plain text line', '%plain text line\n\n'),
        ('''
%blockquote<
    %div
        foo
''', '''
<blockquote><div>
        foo

</div></blockquote>
'''),
        ('''
%img
%img>
%img
''', '''
<img /><img /><img />

'''),
        ('''
%img
%pre><
    foo
    bar
%img
''', '''
<img /><pre>foo
    bar</pre><img />

'''),
        ('''
:javascript
    $(function() {
        alert("hello world!");
    });
    // hello
''', '''
<script type="text/javascript">
    $(function() {
        alert("hello world!");
    });
    // hello

</script>

'''),
        ('%p= "Foo\\nBar"', '<p>{{ "Foo\\nBar" }}</p>\n\n'),
        ('''
%p
    {{ var }}
''', '''
<p>
    {{ var }}

</p>
'''),
        ('- load util', '{% load util %}\n\n'),
        ('''
- if True
    text
''', '''
{% if True %}
    text

{% endif %}
'''),
        ('''
:plain
    / not a comment
    -# will render
    %p
    :javascript
        another depth
''', '''
    / not a comment
    -# will render
    %p
    :javascript
        another depth

'''),
        ('''
:css
    * {margin: 0; padding: 0;}
    .class {
        content: ".";
    }
''', '''
<style type="text/css">
    * {margin: 0; padding: 0;}
    .class {
        content: ".";
    }

</style>

'''),
        ('''!html
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
''', '''<!DOCTYPE html>
{% load util %}
<html>
    <head>
        <title>title of the page</title>
        <link rel="stylesheet" src="static/css/base.css" type="text/css" />
        <link rel="stylesheet" src="{{ STATIC_URL }}css/base.css" type="text/css" />
        <!--[if IE]>
            <link rel="stylesheet" src="{{ STATIC_URL }}css/ie.css" type="text/css" />
        <![endif]-->
    </head>
    <body>
        <!-- html comment -->
        <div id="header">header</div>
        <p>hello world</p>
                <p>second paragraph</p>
        <p class="footnote"></p>
        <blockquote><div>
                Foo!
        </div></blockquote>
        <img />

        <img /><img /><img />

        <p>{{ "Foo\\nBar" }}</p>

        <img /><pre>foo
            bar</pre><img />

        {% if True %}
            <p>
                {{ ONE }}
                {{ TWO }}
                {{ THREE }}
            </p>
        {% endif %}
        <ul>
            <li>{{ one }}</li>
            <li>{{ two }}</li>
            <li>{{ three }}</li>
        </ul>
        <!-- 
            <div>inside</div>
            <div>multi</div>
            <div>line</div>
            <div>comment</div>
         -->
        <!-- 
            text inside
            multi
            line
            comment
         -->
        <p>
            text inside of a
            paragraph block tag
            :javascript
        </p>
        <p>
            <div class="hmm">inline html</div>
        </p>
        <div id="footer">footer</div>
        <script type="text/javascript">
            $(function() {
                alert("hello world!");
            });
            // hello

        </script>

        <script type="text/javascript">
            var a = 1;
            <!-- / hello -->

        </script>
    </body>
</html>
'''),
        )

    def compile_template(self, template):
        stream = StringIO(template)
        outstream = StringIO()
        compiler.Compiler(stream, outstream).compile()
        return outstream.getvalue()

    def test_all(self):
        fail = False
        for template, final in self.cases:
            test_value = self.compile_template(template)
            if test_value != final:
                if fail:
                    print "\n=====================================\n"
                print 'template:\n' + self.re_newline.sub(r'$' + '\n', template)
                print 'compiled:\n' + self.re_newline.sub(r'$' + '\n', test_value)
                print 'expected:\n' + self.re_newline.sub(r'$' + '\n', final)
                fail = True
        if fail:
            raise AssertionError('Expected != Test Got')

if __name__ == '__main__':
    unittest.main()
