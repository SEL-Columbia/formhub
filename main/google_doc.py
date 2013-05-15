import re
import urllib2

from django.template.loader import render_to_string
from django.template.defaultfilters import slugify


class Section(dict):
    """
    A class used to represent a section of a page. A section should
    have certain fields. 'level' denotes how nested this section is in
    the document, like h1, h2, etc. 'id' is a string used to link to
    this section. 'title' will be printed at the top the
    section. 'content' is the html that will be printed as the meat of
    the section. Notice that we use the 'section.html' template to
    render a section as html, and the url provides a link that will be
    used in the page's table of contents.
    """

    FIELDS = ['level', 'id', 'title', 'content']

    def to_html(self):
        return render_to_string('section.html', self)

    def url(self):
        return u'<a href="#%(id)s">%(title)s</a>' % self


class TreeNode(list):
    """
    This simple tree class will be used to construct the table of
    contents for the page.
    """

    def __init__(self, value=None, parent=None):
        self.value = value
        self.parent = parent
        list.__init__(self)

    def add_child(self, value):
        child = TreeNode(value, self)
        self.append(child)
        return child


class GoogleDoc(object):
    """
    This class provides a structure for dealing with a Google
    Document. Most use cases will initialize a GoogleDoc by passing a
    url to the init. This should be a public url that links to an html
    version of the document. You can find this url by publishing your
    Google Document to the web and copying the url.

    The primary method this class provides is 'to_html' which renders
    this document as html in the Twitter Bootstrap format.
    """

    def __init__(self, url=None):
        if url is not None:
            self.set_html_from_url(url)

    def set_html_from_url(self, url):
        f = urllib2.urlopen(url)
        self.set_html(f.read())
        f.close()

    def set_html(self, html):
        """
        When setting the html for this Google Document we do two
        things:

        1. We extract the content from the html. Using a regular
           expression we pull the meat of the document out of the body
           of the html, we also cut off the footer Google adds on
           automatically.

        2. We extract the various sections from the content of the
           document. Again using a regular expression, we look for h1,
           h2, ... tags to split the document up into sections. Note:
           it is important when you are writing your Google Document
           to use the heading text styles, so this code will split
           things correctly.
        """
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
        """
        Make relative paths for images absolute.
        """
        def repl(m):
            return re.sub('src="',
                          'src="https://docs.google.com/document/',
                          m.group(1))

        self._content = re.sub(r'(<img[^>]*>)', repl, self._content)

    def _extract_sections(self):
        """
        Here is an example of what a section header looks like in the
        html of a Google Document:

        <h3 class="c1"><a name="h.699ffpepx6zs"></a><span>Hello World</span></h3>

        We split the content of the Google Document up using a regular
        expression that matches the above header. re.split is a pretty
        cool function if you haven't tried it before. It puts the
        matching groups into the list as well as the content between
        the matches. Check it out here:

        http://docs.python.org/library/re.html#re.split

        One big thing we do in this method is replace the ugly section
        id that Google creates with a nicely slugified version of the
        section title. This makes for pretty urls.
        """
        self._sections = []
        header = r'<h(?P<level>\d) class="[^"]+">' \
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
                title=l.pop(0).decode('utf8'),
                content=l.pop(0),
                )
            section['id'] = slugify(section['title'])
            if section['level'] >= 1:
                self._sections.append(section)

    def _construct_section_tree(self):
        """
        For some weird reason Google Documents doesn't like nesting
        lists, so their table of contents requires a bunch of special
        formatting. Instead of trying to hack off what they provide
        us, we create a tree of sections based on each sections
        level. This tree will be used to construct the html for the
        table of contents.
        """
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
        """
        Return an html representation of the table of contents for
        this document. This is done recursively adding on a list item
        for each element in the tree, and an unordered list if this
        node has children. I might want to double check that this html
        is the correct way to nest lists.
        """
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
        """
        Render the navigation html as a Twitter Bootstrap section.
        """
        return render_to_string('section.html', {
                'level': 1,
                'id': 'contents',
                'title': 'Contents',
                'content': self._navigation_list(),
                })

    def to_html(self):
        """
        Return a cleaned up HTML representation of this Google
        Document.
        """
        return render_to_string('google_doc.html', {
                'nav': self._navigation_html(),
                'content': '\n'.join([s.to_html() for s in self._sections]),
                })
