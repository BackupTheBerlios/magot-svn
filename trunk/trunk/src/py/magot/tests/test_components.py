from peak.api import *
    
SPAM_PROPERTY = PropertyName("simplecmpApp.spam")
COLOR_PROPERTY = PropertyName("simplecmpApp.color")
EGGS_PROPERTY = PropertyName("simplecmpApp.eggs")
    
#------------------------------------------------------------
class ISpam(protocols.Interface):
    """Spam interface"""
    def spam():
        """provide spam"""
  
#------------------------------------------------------------
class IEggs(protocols.Interface):
    """Eggs interface"""
    def eggs():
        """provide eggs"""

class Spam(binding.Component):
    protocols.advise(instancesProvide=[ISpam])
    cEggs = binding.Obtain(IEggs)
    def spam(self):
        return "spam"

class Eggs(binding.Component):
    protocols.advise(instancesProvide=[IEggs])
    def eggs(self):
        return "eggs"

class OtherEggs(binding.Component):
    protocols.advise(instancesProvide=[IEggs])
    def eggs(self):
        return "othereggs"

#------------------------------------------------------------
class GrandChildCmp(binding.Component):
    gcStr = binding.Obtain("sc_string")
    gcSpam = binding.Obtain(SPAM_PROPERTY)
    gcColor = binding.Obtain(COLOR_PROPERTY)
    gcEggs = binding.Obtain(EGGS_PROPERTY)
    gcOtherEggs = binding.Obtain(IEggs)
    
class ChildCmp(binding.Component):
    cStr = binding.Obtain("sc_string")
    cSpam = binding.Obtain(ISpam)
    cEggs = binding.Make(OtherEggs, offerAs=[IEggs])
    grandChild = binding.Make(GrandChildCmp)

class SimpleCmp(binding.Component):
    sc_string = "simple-c!"
    eggs = binding.Make(Eggs, offerAs=[IEggs, EGGS_PROPERTY], uponAssembly=True)
    __spam = binding.Make(Spam, offerAs=[ISpam, SPAM_PROPERTY], uponAssembly=True)
    __color = binding.Make(lambda:"red", offerAs=[COLOR_PROPERTY])
    child = binding.Make(ChildCmp)


if __name__ == "__main__":
    
    sc = SimpleCmp()
    c = sc.child
    gc = c.grandChild
    
    print "c.eggs: ",c.cEggs.eggs()
    print "c.spam: ",c.cSpam.spam()
    print "gc.spam: ",gc.gcSpam.spam()
    print "gc.eggs: ",gc.gcEggs.eggs()
    print "gcOther.eggs: ",gc.gcOtherEggs.eggs()
    print "c.spam.eggs: ",c.cSpam.cEggs.eggs()

    print c.cSpam.cEggs
    print sc.eggs
    sc.eggs=Eggs()
    print sc.eggs
    print c.cSpam.cEggs
    del sc.eggs
    sc.eggs
    print sc.eggs
    print c.cSpam.cEggs

    print "done"
