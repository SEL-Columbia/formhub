QUESTION_TYPES_TO_EXCLUDE = [
    u'note',
]


def question_types_to_exclude(_type):
    return _type in QUESTION_TYPES_TO_EXCLUDE


class DictOrganizer(object):
    def set_dict_iterator(self, dict_iterator):
        self._dict_iterator = dict_iterator

    # Every section will get its own table
    # I need to think of an easy way to flatten out a dictionary
    # parent name, index, table name, data
    def _build_obs_from_dict(self, d, obs, table_name,
                             parent_table_name, parent_index):
        if table_name not in obs:
            obs[table_name] = []
        this_index = len(obs[table_name])
        obs[table_name].append({
            u"_parent_table_name" : parent_table_name,
            u"_parent_index" : parent_index,
            })
        for k, v in d.items():
            if type(v)!=dict and type(v)!=list:
                assert k not in obs[table_name][-1]
                obs[table_name][-1][k] = v
        obs[table_name][-1][u"_index"] = this_index

        for k, v in d.items():
            if type(v)==dict:
                kwargs = {
                    "d" : v,
                    "obs" : obs,
                    "table_name" : k,
                    "parent_table_name" : table_name,
                    "parent_index" : this_index
                    }
                self._build_obs_from_dict(**kwargs)
            if type(v)==list:
                for i, item in enumerate(v):
                    kwargs = {
                        "d" : item,
                        "obs" : obs,
                        "table_name" : k,
                        "parent_table_name" : table_name,
                        "parent_index" : this_index,
                        }
                    self._build_obs_from_dict(**kwargs)
        return obs

    def get_observation_from_dict(self, d):
        result = {}
        assert len(d.keys())==1
        root_name = d.keys()[0]
        kwargs = {
            "d" : d[root_name],
            "obs" : result,
            "table_name" : root_name,
            "parent_table_name" : u"",
            "parent_index" : -1,
            }
        self._build_obs_from_dict(**kwargs)
        return result
