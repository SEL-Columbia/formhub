class SectionIncludeError(Exception):
    def __init__(self, container, include_slug):
        self.container = container
        self.include_slug = include_slug


class IncludeNotFound(SectionIncludeError):
    def __repr__(self):
        return "The section '%s' was not able to include the section '%s'" % \
                    (self.container, self.include_slug)


class CircularInclude(SectionIncludeError):
    def __repr__(self):
        return "The section '%s' detected a circular include of section '%s'" % \
                    (self.container, self.include_slug)
