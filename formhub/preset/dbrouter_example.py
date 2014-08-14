""" Database router sending any models listed in "GisTableNames" to the 'gis' database

"""

GisTableNames = {'Data_Load_Log', 'CDC_Data', 'Spell_Correct'}

class GisRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.object_name in GisTableNames:
            return 'gis'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.object_name in GisTableNames:
            return 'gis'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # relations are allowed when both tables are in the second db, or when neither is
        # (tested using the size of the intersection of the two sets)
        objs = {obj1, obj2}
        return len(objs & GisTableNames) != 1

    def allow_syncdb(self, db, model):
        if model._meta.object_name in GisTableNames:
            return db == 'gis'
        else:
            return db != 'gis'
