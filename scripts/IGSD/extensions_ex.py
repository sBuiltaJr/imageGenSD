#####  Imports  #####

from modules import script_callbacks

def grab_image(img_info):
    img_info.image.show()

script_callbacks.on_before_image_saved(grab_image)