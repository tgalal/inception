from .maker_image import ImageMaker
class RecoveryImageMaker(ImageMaker):
    def __init__(self, config):
        super(RecoveryImageMaker, self).__init__(config, "recovery", "recovery")