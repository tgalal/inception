import argparse
from inception.inceptionobject import InceptionObject
class InceptionArgParser(argparse.ArgumentParser, InceptionObject):
    def __init__(self, *args, **kwargs):
        super(InceptionArgParser, self).__init__(*args, **kwargs)
        self.time = True

    def trackTime(self):
        return self.time

    def getArgs(self):
        return self.parse_args()

    def process(self):
        self.args = vars(self.parse_args())
