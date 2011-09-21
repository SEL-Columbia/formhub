# I'm going to move all that data dictionary work that has been done
# in odk_logger.models.XForm over to here.

class OldXFormParser(object):
    def __init__(self, xml):
        assert type(xml)==str or type(xml)==unicode, u"xml must be a string"
        self.doc = minidom.parseString(xml)
        self.root_node = self.doc.documentElement

    def get_variable_list(self):
        """
        Return a list of pairs [(path to variable1, attributes of variable1), ...].
        """
        bindings = self.doc.getElementsByTagName(u"bind")
        attributes = [dict(_all_attributes(b)) for b in bindings]
        # note: nodesets look like /water/source/blah we're returning source/blah
        return [(SLASH.join(d.pop(u"nodeset").split(SLASH)[2:]), d) for d in attributes]

    def get_variable_dictionary(self):
        d = {}
        for path, attributes in self.get_variable_list():
            assert path not in d, u"Paths should be unique."
            d[path] = attributes
        return d

    def follow(self, path):
        """
        Path is an array of node names. Starting at the document
        element we follow the path, returning the final node in the
        path.
        """
        element = self.doc.documentElement
        count = {}
        for name in path.split(SLASH):
            count[name] = 0
            for child in element.childNodes:
                if isinstance(child, minidom.Element) and child.tagName==name:
                    count[name] += 1
                    element = child
            assert count[name]==1
        return element

    def get_id_string(self):
        """
        Find the single child of h:head/model/instance and return the
        attribute 'id'.
        """
        instance = self.follow(u"h:head/model/instance")
        children = [child for child in instance.childNodes \
                        if isinstance(child, minidom.Element)]
        assert len(children)==1
        return children[0].getAttribute(u"id")

    def get_title(self):
        title = self.follow(u"h:head/h:title")
        assert len(title.childNodes)==1, u"There should be a single title"
        return title.childNodes[0].nodeValue

    supported_controls = ["input", "select1", "select", "upload"]

    def get_control_dict(self):
        def get_pairs(e):
            result = []
            if hasattr(e, "tagName") and e.tagName in self.supported_controls:
                result.append( (e.getAttribute("ref"),
                                get_text(follow(e, "label").childNodes)) )
            if e.hasChildNodes:
                for child in e.childNodes:
                    result.extend(get_pairs(child))
            return result
        return dict(get_pairs(self.follow("h:body")))


# these cleaners will be used when saving data
# All cleaned types should be in this list
cleaner = {
    u'geopoint': lambda(x): dict(zip(
            ["latitude", "longitude", "altitude", "accuracy"],
            x.split()
            )),
    u'dateTime': lambda(x): datetime.datetime.strptime(
        x.split(".")[0],
        '%Y-%m-%dT%H:%M:%S'
        ),
    }

class XFormParser(XForm):

    class Meta:
        app_label = "odk_viewer"
        proxy = True

    def guarantee_parser(self):
        # there must be a better way than this solution
        if not hasattr(self, "parser"):
            self.parser = OldXFormParser(self.xml)

    def clean_instance(self, data):
        """
                1. variable doesn't start with _
                2. if variable doesn't exist in vardict log message
                3. if there is data and a cleaner, clean that data
        """            
        self.guarantee_parser()
        vardict = self.parser.get_variable_dictionary()
        for path in data.keys():
            if not path.startswith(u"_") and data[path]:
                if path not in vardict:
                    raise Exception(
                        "The XForm %(id_string)s does not describe all "
                        "the variables seen in this instance. "
                        "Specifically, there is no definition for "
                        "%(path)s." % {
                            "id_string" : self.id_string,
                            "path" : path
                            }
                        )
                elif vardict[path][u"type"] in cleaner:
                    data[path] = cleaner[vardict[path][u"type"]](data[path])
        
