import abc
class IdentifierResolver(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def resolve(self, identifier):
        pass