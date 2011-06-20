class NoMongoException(Exception):
    def __init__(self):
        super(NoMongoException, self).__init__("Mongo is being phased out")
