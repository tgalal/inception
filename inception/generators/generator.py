from inception.inceptionobject import InceptionObject
class GenerationFailedException(Exception):
    pass

class Generator(InceptionObject):
    def __init__(self):
        super(Generator, self).__init__()

    def generate(self):
        pass