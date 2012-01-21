# Since we don't know what SDK they're using, and I don't particularly want to implement the code that looks for superclasses, we can just hardcode in some commonly overridden selectors
IGNORED_SELECTORS = set([
    "+allocWithZone:",
    "+copyWithZone:",
    "+load",
    "+initialize",

    "-compare:",
    "-isEqual:",
    "-hash",
    "-description",
    "-awakeFromNib",
    "-setValue:forKey:",
    "-valueForKey:",
    
    "-numberOfRowsInTableView:",
    "-tableView:objectValueForTableColumn:row:",
    "-tableView:setObjectValue:forTableColumn:row:",
    
    "-init",
    "-dealloc",
    "-finalize",
    "-drawRect:",
    "-mouseDown:",
    "-mouseUp:",
    "-mouseDragged:",
    "-mouseMoved:",
    "-keyDown:",
    "-keyUp:",
])

def analyze(root, files, defs):
    # Sort by class name
    classes = {}
    for d in defs:
        n = d['name']
        if n in classes:
            classes[n].append(d)
        else:
            classes[n] = [d]
    
    results = []
    for n in classes:
        # Find missing methods
        missing_dict = analyze_missing_methods(n, classes[n])
        if missing_dict:
            results.append(missing_dict)
    return results

def analyze_missing_methods(name, objs):
    # Is there an implementation here?
    imps = find_with_key(objs, 'type', '@implementation')
    if len(imps) != 1:
        return None
    imp = imps[0]
    impsels = imp['selectors']
    missingsels = impsels.copy()
    
    intfs = find_with_key(objs, 'type', '@interface')
    isgood = True
    for intf in intfs:
        intfsels = intf['selectors']
        
        missingsels.difference_update(intfsels)
        # missingsels -= intfsels
    
    missingsels.difference_update(IGNORED_SELECTORS)
    
    for missingsel in missingsels:
        print '%s is missing: %s' % (name, missingsel)
        isgood = False
    
    if len(missingsels) == 0:
        return None
        
    return {
        'name': name,
        'implementation': imp,
        'missing': missingsels,
    }
    
def find_with_key(objs, k, v):
    return [o for o in objs if o[k] == v]
def find_with_kind(objs, kind):
    return [o for o in objs if o['kind'] == kind]
    
    