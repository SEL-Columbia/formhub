import os
from xform_fs import XFormInstanceFS

def iterate_through_odk_instances(dirpath, callback):
    count = 0
    for directory, subdirs, subfiles in os.walk(dirpath):
        for filename in subfiles:
            filepath = os.path.join(directory, filename)
            if XFormInstanceFS.is_valid_odk_instance(filepath):
                xfxs = XFormInstanceFS(filepath)
                count += callback(xfxs)
                del(xfxs)
    return count