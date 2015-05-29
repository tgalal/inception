from .maker_image import ImageMaker
from inception.constants import InceptionConstants
class BootImageMaker(ImageMaker):
    def __init__(self, config):
        super(BootImageMaker, self).__init__(config, "boot", InceptionConstants.OUT_NAME_BOOT)
