import json

def make_adjustment(base_sections, section_dict, action):
    """
    This receives the parent's list and the item that is to be reordered.
    It then returns the altered parent's include list to reflect the "action"
    that was requested.
    
    This can probably be taken out if/when we find a better/simpler way to do
    this.
    """
    new_sections = base_sections
    if action == 'activate':
        new_sections = base_sections + [section_dict]
    elif action in ['up', 'down']:
        i = base_sections.index(section_dict)
        new_sections = filter(lambda x: x != section_dict, base_sections)
        delta = 0
        if action == 'up':
            delta = -1
        elif action == 'down':
            delta = 1
        new_sections.insert(i + delta, section_dict)
    elif action in ['delete', 'deactivate']:
        new_sections = filter(lambda x: x != section_dict, base_sections)
    else:
        raise Exception('Action [%s] was not understood' % action)
    return new_sections
