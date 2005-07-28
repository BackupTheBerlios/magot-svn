from peak.api import *

# ###############################################################
# DATA CONSOLIDATION FROM MUTIPLE PROVIDERS INTO A SINGLE CONSUMER.
# EACH NODE OF THE HIERARCHY CAN HAVE ITS OWN CONSOLIDATION.
# ###############################################################

# ######################################################################
# DATA DIFFUSION FROM A PROVIDER TO A CONSUMER HIERARCHY.
# EACH CONSUMER NODE CAN OVERRIDE THE PULLED VALUE AND PUBLISH THE
# MODIFIED VALUE TO ITS OWN SUB-HIERARCHY.
# ######################################################################

# ############### Machinery #######################

class ComputedEvenIfSet(model.Attribute):    
    """ Value is computed first. Return computed value only if not None. 
        Else return local value.
    """
    def get(feature, element):
        res = feature.compute(element)
        if res is not None:
            return res
        else:
            return element.__dict__.get(feature.attrName, None)
    def compute(feature, element):
        raise NotImplementedError

class Node(model.Element):
    """ parent <--> children relationship."""
    class parent(model.Attribute):
        referencedType = 'Node'
        referencedEnd = 'children'
        defaultValue = None
    class children(model.Collection):
        referencedType = 'Node'
        referencedEnd = 'parent'
        singularName = 'child'

class ComputedOnlyWhenNotSet(model.Attribute):
    """ Value is computed only when it's not locally set. """
    def get(feature, element):
        try:
            return element.__dict__[feature.attrName]
        except KeyError:
            return feature.compute(element)
    def compute(feature, element):
        raise NotImplementedError

class GetFromParentWhenNotSet(ComputedOnlyWhenNotSet):
    """ Pull value from parent when not locally set. """
    def compute(feature, element):
        if element.parent is None:
            return None
        else:
            return getattr(element.parent, feature.attrName)


# ############### attribute formula #######################

def getOnLocal(name):
    class attr(model.Attribute):
        pass
    attr.attrName = name
    return attr

def getOnParent(name):
    class attr(GetFromParentWhenNotSet):
        pass
    attr.attrName = name
    return attr

def getOnGold(name):
    class attr(ComputedEvenIfSet):
        def compute(feature, element):
            goldAttr = getOnGold(name)
            try:
                value = goldAttr.get(element.manual)
                if value is not None:
                    return value
            except AttributeError:
                pass 
            try:
                value = goldAttr.get(element.reuters)
                if value is not None:
                    return value
            except AttributeError:
                return None
    attr.attrName = name
    return attr

def getOnGoldOrOnParent(name):
    class attr(ComputedEvenIfSet):
        def compute(feature, element):
            value = getOnGold(name).get(element)
            if value is None:
                value = getOnParent(name).get(element)
            return value
    attr.attrName = name
    return attr


# ############### TEMPLATE OF OBJECTS #######################

class SUPER_OPTION_CONTRACT(Node, model.Element):
    # TODO: try to gess the name from the function result 
    cycle = getOnGold('cycle')
    year = getOnGold('year')
class MA_SUPER_OPTION_CONTRACT(model.Element):
    cycle = getOnLocal('cycle')
    year = getOnLocal('year')
class RT_SUPER_OPTION_CONTRACT(model.Element):
    cycle = getOnLocal('cycle')

class OPTION_CONTRACT(Node, model.Element):
    cycle = getOnGoldOrOnParent('cycle')
    year = getOnGoldOrOnParent('year')
class MA_OPTION_CONTRACT(model.Element):
    cycle = getOnLocal('cycle')
    year = getOnLocal('year')
class RT_OPTION_CONTRACT(model.Element):
    cycle = getOnLocal('cycle')

class OPTION(Node, model.Element):
    cycle = getOnGoldOrOnParent('cycle')
    year = getOnGoldOrOnParent('year')
class MA_OPTION(model.Element):
    cycle = getOnLocal('cycle')
    year = getOnLocal('year')
class RT_OPTION(model.Element):
    cycle = getOnLocal('cycle')


if __name__ == '__main__':
       
    super = SUPER_OPTION_CONTRACT()
    assert super.cycle is None
    super.reuters = RT_SUPER_OPTION_CONTRACT(cycle="rt super")
    assert super.cycle == super.reuters.cycle
    super.manual = MA_SUPER_OPTION_CONTRACT(cycle="ma super",year="2005")
    assert super.cycle == super.manual.cycle
    assert super.year == super.manual.year


    contract = OPTION_CONTRACT()
    assert contract.cycle is None  # due to no child to consolidate from
    contract.parent = super # give it a parent to get any value from
    # consolidated value is None so get the value from parent
    assert contract.cycle == contract.parent.cycle
    contract.reuters = RT_OPTION_CONTRACT(cycle="rt contract")
    # consolidation is done so the consolidated value is used
    assert contract.cycle == contract.reuters.cycle
    contract.manual = MA_OPTION_CONTRACT(cycle="ma contract")
    assert contract.cycle == contract.manual.cycle
    contract.manual.cycle = None
    assert contract.cycle == contract.reuters.cycle
    contract.reuters.cycle = None
    # consolidated value is None so get the value from parent
    assert contract.cycle == super.cycle
    assert contract.year == super.year


    option = OPTION()
    assert option.cycle is None  # due to no child to consolidate from
    option.parent = contract # give it a parent to get any value from
    # consolidated value is None so get the value from parent
    assert option.cycle == option.parent.cycle
    assert option.year == contract.year
    option.reuters = RT_OPTION_CONTRACT(cycle="rt option")
    # consolidation is done so the value is consolidated from the right provider
    assert option.cycle == option.reuters.cycle
    option.manual = MA_OPTION_CONTRACT(cycle="ma option")
    assert option.cycle == option.manual.cycle
    option.manual.cycle = None
    assert option.cycle == option.reuters.cycle
    option.reuters.cycle = None
    # consolidated value is None so get the value from parent
    assert option.cycle == option.parent.cycle
    assert option.year == option.parent.year
    # let parent consolidated and get this parent consolidated value
    option.parent.manual.year = "ma contract 2005"
    assert option.parent.year == "ma contract 2005"
    assert option.year == option.parent.year
    option.manual.year = "ma option 2005"
    assert option.year == option.manual.year == "ma option 2005"
