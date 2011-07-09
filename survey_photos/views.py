from django.http import HttpResponse, HttpResponseRedirect

from photo_sizes import AVAILABLE_SIZES

IMG_STORE_URL = "/static/survey_photos"
IMAGE_NOT_FOUND_URL = "%s/image_not_found.jpg" % IMG_STORE_URL

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_STORE_DIRECTORY = os.path.join(CURRENT_DIR, 'img_storage')

class ImageNotFoundException(Exception):
    pass

def photo_redirect(request, size, photo_id):
    img_path = os.path.join(IMG_STORE_DIRECTORY, size, photo_id)
    image_url = "%s/%s/%s" % (IMG_STORE_URL, size, photo_id)
    try:
        if size not in AVAILABLE_SIZES:
            raise ImageNotFoundException("Image not found")
        if not os.path.exists(img_path):
            raise ImageNotFoundException("Image not found")
        return HttpResponseRedirect(image_url)
    except ImageNotFoundException, e:
        return HttpResponseRedirect(IMAGE_NOT_FOUND_URL)
