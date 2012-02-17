import re
import scanner
import os
import parser

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
    
    
    #analyze_missing_imports(classes, defs)
    #return
    
    results = []
    for n in classes:
        # Find missing methods
        missing_dict = analyze_missing_methods(n, classes[n])
        if missing_dict:
            results.append(missing_dict)
    return results

def analyze_missing_imports(classes, objs):
    classfindingregex = r'[^a-zA-Z0-9_]([A-Z][a-zA-Z0-9_]{3,})[^a-zA-Z0-9_]'
    
    existing_classes = set(c for c in classes)
    
    for o in objs:
        if o['type'] == '@interface' or o['type'] == '@implementation':
            body = o['body']
            found_classes = set(re.findall(classfindingregex, body)) & existing_classes
            o['found_classes'] = found_classes
        

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

def analyze2(root, files, defs):
    # We need to build up a big old database
    # 1. A set of header files
    header_files = files['header_paths']
    
    # 2. A set of implementation files
    imp_files = files['imp_paths']
    
    # 3. For each of the above, which symbols it declares, and which symbols it uses
    declarations = {}
    dx = set(d['name'] for d in defs)
    for d in defs:
        f = d['subpath']
        if f not in declarations:
            declarations[f] = set()
        declarations[f].add(d['name'])
    
    uses = {}
    for f in header_files:
        uses[f] = parser.find_uses(root, f, dx)
    for f in imp_files:
        uses[f] = parser.find_uses(root, f, dx)
        # A imp needs everything in its header
        for h in header_files:
            hext = os.path.splitext(h)[0]
            fext = os.path.splitext(f)[0]
            if fext == hext:
                uses[f] |= uses[h]
                break
        
    # 4. Find imports, includes, etc
    for f in header_files | imp_files:
        includes = parser.find_includes(root, f)
        #print includes
        for incf in includes['#import']:
            # Find all declarations
            for df in declarations:
                if df == incf or df.endswith('/' + incf) or incf.endswith('/' + df):
                    uses[f] -= declarations[df]
        uses[f] -= set(includes['@class'])
            
    # Remove things which are already declared
    for f in declarations:
        ds = declarations[f]
        uses[f] -= ds
        print 'uses[%s] => %s' % (f, uses[f])
    
    # 5. A map of symbols to their files
    symbols_to_files = {}
    for k in declarations:
        for x in declarations[k]:
            symbols_to_files[x] = k
        
    return {
        'header_files': header_files,
        'imp_files': imp_files,
        'declarations': declarations,
        'uses': uses,
        'symbols_to_files': symbols_to_files,
    }


def find_with_key(objs, k, v):
    return [o for o in objs if o[k] == v]
def find_with_kind(objs, kind):
    return [o for o in objs if o['kind'] == kind]
    
    