from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect

class ViewNav(object):
    def __init__(self, name, url):
        self.url = url
        self.name = name

class ViewPkgr(object):
    """
    A tool to package up the things we need to include
    with render_to_response. This should make it easier to 
    use consistent features (e.g. navigation) throughout
    the site.
    """
    def __init__(self, request, template):
        self.req = request
        self.template = template
        self.info = {}
        self.navigation_items = []
        self._display_footer = False
        self.redirect_to = None
        self.template = template
        self._extends_template = "_extends_base.html"
    
    def footer(self, display_footer=True):
        self._display_footer = display_footer
        
    def ensure_logged_in(self):
        if not self.req.user.is_authenticated():
            self.redirect_to = "/accounts/login/"
        
    def nav(self, item):
        if isinstance(item, ViewNav):
            self.navigation_items.append(item)
        else:
            self.navigation_items.append(ViewNav(*item))
    
    def add_info(self, uinfo):
        self.info.update(uinfo)
        
    def as_popup(self):
        self._extends_template = "_extends_popup.html"

    def navs(self, items):
        [self.nav(i) for i in items]
    
    def r(self):
        if self.redirect_to is not None:
            return HttpResponseRedirect(self.redirect_to)
        self.info['navs'] = self.navigation_items
        self.info['user'] = self.req.user
        self.info['display_footer'] = self._display_footer
        self.info['template_to_include'] = self.template
        return render_to_response(self._extends_template, self.info)