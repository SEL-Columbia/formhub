
def gather_includes(section=[], includes_dict={}, destination=[]):
    for q in section:
        if q[u'type'] == u'include':
            include_name = q[u'name']
            inner_section = includes_dict.pop(include_name, None)
            if inner_section != None:
                gather_includes(section=inner_section,
                    includes_dict=includes_dict, destination=destination)
        else:
            destination.append(q)
    return destination
