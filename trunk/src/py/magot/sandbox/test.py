from peak.api import *

class E(model.Element):
    class name(model.Attribute):
        pass
e=E(name="toto")
e.name
class B(model.Attribute):
    pass

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

class ComputedEvenIfSet(model.Attribute):    
    """ Value is computed first. Return computed value only if not None. 
        Else return local value if set or None.
    """
    def get(feature, element):
        res = feature.compute(element)
        if res is not None:
            return res
        else:
            return element.__dict__.get(feature.attrName, None)
    def compute(feature, element):
        raise NotImplementedError

class ComputedOnlyWhenNotSet(model.Attribute):
    """ Value is computed only if it's not locally set. """
    def get(feature, element):
        try:
            return element.__dict__[feature.attrName]
        except KeyError:
            return feature.compute(element)
    def compute(feature, element):
        raise NotImplementedError

def getValue(feature, element, formula=None):
    if formula is not None:
        formula.attrName = feature.attrName
        value = formula.get(element)
    else:
        value = getattr(element, feature.attrName)

    return value


# ############### attribute formula #######################

class OnLocal(model.Attribute):
    pass

class OnParent(ComputedOnlyWhenNotSet):
    """ Pull value from parent when not locally set. """
    def compute(feature, element):
        if element.parent is None:
            return None
        else:
            return getValue(feature, element.parent)

class OnGold(ComputedEvenIfSet):
    """ Pull value from children 'manual' or 'reuters'. 
        Return this value if found or None if not found.
    """
    def compute(feature, element):
        try:
            value = getValue(feature, element.manual)
            if value is not None:
                return value
        except AttributeError:
            pass # no manual child
        try:
            value = getValue(feature, element.reuters)
        except AttributeError:
            return None # no reuters child
        return value

class OnGoldOrOnParent(ComputedEvenIfSet):
    def compute(feature, element):
        value = getValue(feature, element, OnGold)
        if value is None:
            value = getValue(feature, element, OnParent)
        return value

class OnGrandParent(ComputedEvenIfSet):
    def compute(feature, element):
        value = getValue(feature, element.parent, OnParent)
        return value


# ############### TEMPLATE OF OBJECTS #######################

class SUPER_OPTION_CONTRACT(Node, model.Element):
    class cycle(OnGold):pass
    class year(OnGold):pass

class MA_SUPER_OPTION_CONTRACT(model.Element):
    class cycle(OnLocal):pass
    class year(OnLocal):pass

class RT_SUPER_OPTION_CONTRACT(model.Element):
    class cycle(OnLocal):pass



class OPTION_CONTRACT(Node, model.Element):
    class cycle(OnGoldOrOnParent):pass
    class year(OnGoldOrOnParent):pass

class MA_OPTION_CONTRACT(model.Element):
    class cycle(OnLocal):pass
    class year(OnLocal):pass

class RT_OPTION_CONTRACT(model.Element):
    class cycle(OnLocal):pass



class OPTION(Node, model.Element):
    class cycle(OnGoldOrOnParent):pass
    class year(OnGoldOrOnParent):pass

class MA_OPTION(model.Element):
    class cycle(OnLocal):pass
    class year(OnLocal):pass

class RT_OPTION(model.Element):
    class cycle(OnLocal):pass
    class year(OnGrandParent):pass


if __name__ == '__main__':

    # Test consolidation on parent from child values
    super = SUPER_OPTION_CONTRACT()
    assert super.cycle is None
    super.reuters = RT_SUPER_OPTION_CONTRACT(cycle="rt super")
    assert super.cycle == super.reuters.cycle
    super.manual = MA_SUPER_OPTION_CONTRACT(cycle="ma super", year="2005")
    assert super.cycle == super.manual.cycle  # manual has priority over reuters
    assert super.year == super.manual.year

    # Test propagation of parent values to children
    contract = OPTION_CONTRACT()
    assert contract.cycle is None   # due to no child to consolidate from
    contract.parent = super         # give it a parent to get any value from it
    # as consolidated value is None, then get the value from parent
    assert contract.cycle == contract.parent.cycle
    contract.reuters = RT_OPTION_CONTRACT(cycle="rt contract")
    # consolidation ok so the consolidated value is used instead of parent value
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
    option.reuters = RT_OPTION(cycle="rt option")
    # consolidation is done so the value is consolidated from the right provider
    assert option.cycle == option.reuters.cycle
    option.manual = MA_OPTION(cycle="ma option")
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

    super.year = "super 2005"
    option.year == super.year
   
