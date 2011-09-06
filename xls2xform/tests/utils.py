
def _sn(*args):
    o = []
    for a in args:
        if u'name' in a:
            o.append(a[u'name'])
        else:
            o.append(a.split(':'))[1]
    return o

def _qd(*args):
    # include question json. convert type:name to a dict: {type: name}
    # used only in testing.
    ql = [t.split(':') for t in args]
    return [{u'type': unicode(tt[0]), u'name': unicode(tt[1])} for tt in ql]

def _names_as_strings(ss):
    """
    Takes a section and returns a list of names.
    Used only in tests.
    """
    return [s[u'name'] for s in ss._children]
