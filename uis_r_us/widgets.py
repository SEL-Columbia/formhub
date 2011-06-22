WIDGETS_BY_REGION_LEVEL = [
        #country:
        ["country"],
        #state:
        ["regnav_state", "state_map", "state_mdg_performance"],
        #lga:
        ["lga_facilities"]
]

def widget_includes_by_region_level(scope):
    i = ["country", "state", "lga"].index(scope)
    wslugs = WIDGETS_BY_REGION_LEVEL[i]
    widget_ids = []
    include_templates = []
    for w in wslugs:
        widget_ids.append(w)
        include_templates.append(u"widgets/%s.html" % w)
    return (widget_ids, include_templates)

import widget_defs

def embed_widgets(context, scope="country"):
    widget_ids, include_templates = widget_includes_by_region_level(scope)
    for w in widget_ids:
        if hasattr(widget_defs, w):
            context.__dict__[w] = getattr(widget_defs, w)(context=context)
        else:
            context.__dict__[w] = False
    context.widgets = include_templates
