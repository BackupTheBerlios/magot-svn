from peak.model import features
from peak.binding import attributes


class NewAttribute(object):
    """ Attribute metadata that generates a new attribute whose name is '<attrName>suffix'. """
    def __init__(self, suffix):
        self.suffix = suffix


@attributes.declareAttribute.when(NewAttribute)
def _declareNewAttribute(classobj, attrname, metadata):
    class newAttr(features.Attribute): pass
    newAttrName = attrname + metadata.suffix
    newAttr.attrName = newAttr.__name__ = newAttrName
    newAttr.activateInClass(classobj, newAttrName)


class DerivedAndCached(features.Attribute):
    """ Attribute whose value is computed only if it's not already set. """

    def get(feature, element):
        try:
            return element.__dict__[feature.attrName]
        except KeyError:
            value = feature.compute(element)
            feature.set(element, value)
            return value

    def compute(feature, element):
        raise NotImplementedError


class Proxy(object):
    """ A Proxy class that delegates to an original object for all untouched attributes
        and stores overridden attributes. 
    """

    def __init__(self, obj):
        """The initializer."""
        super(Proxy, self).__init__(obj)
        # Original object.
        self._obj = obj

    def __getattr__(self, attr):
        try:
            # Is this attribute overridden in the proxy?
            return self.__dict__[attr]
        except KeyError:
            # If not, then return the attribute value from the original object
            return getattr(self._obj, attr)

    def getModifiedAttr(self, attr):
        modified = self.__dict__.get(attr, None)
        try:
            if modified != getattr(self._obj, attr):
                return modified
            else:
                return None
        except AttributeError:
            return modified

    def getOriginalObject(self):
        return self._obj
