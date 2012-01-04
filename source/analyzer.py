def analyze(root, files, defs):
    # Sort by class name
    classes = {}
    for d in defs:
        n = d['name']
        if n in classes:
            classes[n].append(d)
        else:
            classes[n] = [d]
    
    for n in classes:
        # Find missing methods
        analyze_missing_methods(n, classes[n])

def analyze_missing_methods(name, objs):
    # Is there an implementation here?
    imps = find_with_key(objs, 'type', '@implementation')
    if len(imps) != 1:
        return True
    imp = imps[0]
    impsels = imp['selectors']
    missingsels = impsels.copy()
    
    intfs = find_with_key(objs, 'type', '@interface')
    isgood = True
    for intf in intfs:
        intfsels = intf['selectors']
        missingsels -= intfsels
    
    for missingsel in missingsels:
        print '%s is missing: %s' % (name, missingsel)
        isgood = False
    
    return isgood
    
def find_with_key(objs, k, v):
    return [o for o in objs if o[k] == v]
def find_with_kind(objs, kind):
    return [o for o in objs if o['kind'] == kind]
    
    