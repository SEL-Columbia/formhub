import re
import urllib2

from django.template.loader import render_to_string
from django.template.defaultfilters import slugify


class Section(dict):

    FIELDS = ['level', 'id', 'title', 'content']

    def to_html(self):
        return render_to_string('section.html', self)

    def url(self):
        return '<a href="#%(id)s">%(title)s</a>' % self


class TreeNode(list):

    def __init__(self, value=None, parent=None):
        self.value = value
        self.parent = parent
        list.__init__(self)

    def add_child(self, value):
        child = TreeNode(value, self)
        self.append(child)
        return child


class GoogleDoc(object):

    def __init__(self, url=None):
        if url is not None:
            f = urllib2.urlopen(url)
            self.set_html(f.read())
            f.close()

    def set_html(self, html):
        self._html = html
        self._extract_content()
        self._extract_sections()

    def _extract_content(self):
        m = re.search(r'<body>(.*)</div><div id="footer">',
                      self._html,
                      re.DOTALL)
        self._content = m.group(1)
        self._fix_image_urls()

    def _fix_image_urls(self):
        def repl(m):
            # make a relative path for the img src absolute
            return re.sub('src="',
                          'src="https://docs.google.com/document/',
                          m.group(1))

        self._content = re.sub(r'(<img[^>]*>)', repl, self._content)

    def _extract_sections(self):
        self._sections = []
        header = r'<h(?P<level>\d) class="c\d+">' \
            r'<a name="(?P<id>[^"]+)"></a>'      \
            r'<span>(?P<title>[^<]+)</span>'     \
            r'</h\d>'
        l = re.split(header, self._content)
        l.pop(0)
        while l:
            section = Section(
                # hack: cause we started with h3 in google docs
                level=int(l.pop(0)) - 2,
                id=l.pop(0),
                title=l.pop(0),
                content=l.pop(0),
                )
            section['id'] = slugify(section['title'])
            self._sections.append(section)

    def _construct_section_tree(self):
        self._section_tree = TreeNode(Section(level=0))
        current_node = self._section_tree
        for section in self._sections:
            while section['level'] <= current_node.value['level']:
                current_node = current_node.parent
            while section['level'] > current_node.value['level'] + 1:
                empty_section = Section(level=current_node.value['level'] + 1)
                current_node = current_node.add_child(empty_section)
            assert section['level'] == current_node.value['level'] + 1
            current_node = current_node.add_child(section)

    def _navigation_list(self, node=None):
        if node is None:
            self._construct_section_tree()
            return self._navigation_list(self._section_tree)
        result = ""
        if 'title' in node.value and 'id' in node.value:
            result += '<li>%s</li>' % node.value.url()
        if len(node) > 0:
            result += "<ul>%s</ul>" % \
                "\n".join([self._navigation_list(child) for child in node])
        return result

    def _navigation_html(self):
        return render_to_string('section.html', {
                'level': 1,
                'id': 'contents',
                'title': 'Contents',
                'content': self._navigation_list(),
                })

    def to_html(self):
        return render_to_string('google_doc.html', {
                'nav': self._navigation_html(),
                'content': '\n'.join([s.to_html() for s in self._sections]),
                })
