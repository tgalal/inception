from .maker_image import ImageMaker
class BootImageMaker(ImageMaker):
    def __init__(self, config):
        super(BootImageMaker, self).__init__(config, "boot", "boot")
