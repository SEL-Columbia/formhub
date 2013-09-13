import xml.etree.ElementTree as etree

from utils.logger_tools import OpenRosaResponseNotAcceptable

def real_time_action(username, xml_file, uuid, request):

    try:  # (we really need to do our own error processing and not depend on our caller)
        dummy = username
        tree = etree.parse(xml_file)
        root = tree.getroot()
        dummy = uuid
    except:
        raise
    finally:
        xml_file.seek(0)    # reset the file for the next caller


    if False:
        return OpenRosaResponseNotAcceptable(u'this is only a test')###
    return None  # all is well -- continue processing this record
