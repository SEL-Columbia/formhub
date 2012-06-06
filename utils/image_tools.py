from cStringIO import StringIO
from PIL import Image

def get_dimensions((width, height), longest_side):
    if width > height:
        width = longest_side
        height = (height/width) * longest_side
    elif height >width:
        height = longest_side
        width = (width/height) * longest_side
    else:
        height = longest_side
        width = longest_side
    return (width, height)


def _save_thumbnails(image, path, size, suffix, filename=None):
    # If filename is present, resize on s3 fs
    if filename:
        default_storage = get_storage_class()()
        fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
        image.thumbnail(get_dimensions(image.size, size), Image.ANTIALIAS)
        image.save(get_path(path, suffix))

        default_storage.save(get_path(filename, suffix),
                                fs.open(get_path(path, suffix)))
    else:
        image.thumbnail(get_dimensions(image.size, size), Image.ANTIALIAS)
        image.save(get_path(path, suffix))


def resize(filename):
    default_storage = get_storage_class()()
    path = default_storage.url(filename)
    img_file = urllib.urlopen(path)
    im = StringIO(img_file.read())
    img_file.close()
    image = Image.open(im)
    conf = settings.THUMB_CONF

    fs = get_storage_class('django.core.files.storage.FileSystemStorage')()
    loc_path = fs.path(filename)

    [_save_thumbnails(image, loc_path, conf[key]['size'], conf[key]['suffix'],
                                    filename=filename) for key in conf.keys()]


def resize_local_env(filename):
    default_storage = get_storage_class()()
    path = default_storage.path(filename)
    image = Image.open(path)
    conf = settings.THUMB_CONF

    [_save_thumbnails(image, path, conf[key]['size'], conf[key]['suffix'])
                                                        for key in conf.keys()]
