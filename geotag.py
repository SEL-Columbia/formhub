# http://stackoverflow.com/questions/453395/what-is-the-best-way-to-geotag-jpeg-images-with-python

import pyexiv2

def to_deg(value, loc):
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg =  int(abs_value)
    t1 = (abs_value-deg)*60
    min = int(t1)
    sec = round((t1 - min)* 60, 5)
    return (deg, min, sec, loc_value)    

def set_gps_location(file_name, lat, lng):
    """Adds GPS position as EXIF metadata

    Keyword arguments:
    file_name -- image file 
    lat -- latitude (as float)
    lng -- longitude (as float)

    """
    lat_deg = to_deg(lat, ["S", "N"])
    lng_deg = to_deg(lng, ["W", "E"])

    print lat_deg
    print lng_deg

    # convert decimal coordinates into degrees, munutes and seconds
    exiv_lat = (pyexiv2.Rational(lat_deg[0]*60+lat_deg[1],60),pyexiv2.Rational(lat_deg[2]*100,6000), pyexiv2.Rational(0, 1))
    exiv_lng = (pyexiv2.Rational(lng_deg[0]*60+lng_deg[1],60),pyexiv2.Rational(lng_deg[2]*100,6000), pyexiv2.Rational(0, 1))

    exiv_image = pyexiv2.Image(file_name)
    exiv_image.readMetadata()
    exif_keys = exiv_image.exifKeys() 

    exiv_image["Exif.GPSInfo.GPSLatitude"] = exiv_lat
    exiv_image["Exif.GPSInfo.GPSLatitudeRef"] = lat_deg[3]
    exiv_image["Exif.GPSInfo.GPSLongitude"] = exiv_lng
    exiv_image["Exif.GPSInfo.GPSLongitudeRef"] = lng_deg[3]
    exiv_image["Exif.Image.GPSTag"] = 654
    exiv_image["Exif.GPSInfo.GPSMapDatum"] = "WGS-84"
    exiv_image["Exif.GPSInfo.GPSVersionID"] = '2 0 0 0'

    exiv_image.writeMetadata()

from parsed_xforms.models import ParsedInstance
from common_tags import GPS
import re
import os

for pi in ParsedInstance.objects.all():
    d = pi.to_dict()
    if GPS in d and d[GPS] is not None:
        if not re.search(r'^[0-9. ]+$', d[GPS]): continue
        lat, lng, alt, acc = d[GPS].split()
        for attachment in pi.instance.attachments.all():
            image = attachment.media_file
            path = "site_media/" + image.name
            # set_gps_location(path, float(lat), float(lng))
            os.rename(path, "site_media/tagged/" + image.name)
