import parser
import os

def fix(root, defs, results):
    # Map class names to interface dicts
    class_interfaces = {}
    conflicted = []
    for d in defs:
        if d['type'] == '@interface':
            if d['name'] in conflicted:
                continue
            
            if d['name'] in class_interfaces:
                conflicted.append(d['name'])
                del class_interfaces[d['name']]
                continue
            
            class_interfaces[d['name']] = d
    #print conflicted
    #return
    # Get methods
    #print class_interfaces
    
    for result in results:
        n = result['name']
        if n not in class_interfaces or n in conflicted:
            continue
        
        intf = class_interfaces[n]
        selectors = result['missing']
        
        if not selectors or len(selectors) == 0:
            print "oops"
            continue
        
        sel_meth = { parser.selector_from_signature(meth): meth for meth in result['implementation']['methods'] }
            
        filtered_methods = [ sel_meth[selector] for selector in selectors ]
        
        declare_methods(root, filtered_methods, intf)


def declare_methods(root, methods, main_interface):
    
    # Get the full code of the original interface
    original_code = main_interface['body']
    
    # Find a method to insert after (or else find the last } )
    #   1. First try to find the last ';'
    #   2. Then try to find the last '}'
    #   3. Then just insert at the end
    
    insert_idx = original_code.rfind(';')
    if insert_idx == -1:
        insert_idx = original_code.rfind('}')
    else:
        insert_idx += 1
    
    if insert_idx == -1:
        insert_idx = len(original_code)
    else:
        insert_idx += 1
    
    # Insert the methods
    new_methods = '\n\n' + '\n'.join(meth + ';' for meth in methods) + '\n'
    new_code = strinsert(original_code, insert_idx, new_methods)
    
    #print new_code
    #return
    
    # Get the full code of the file
    fullpath = os.path.join(root, main_interface['subpath'])
    f = open(fullpath, 'r')
    contents = f.read()
    f.close()
    f = None
    
    # Replace the original interface with the new one
    new_contents = contents.replace(original_code, new_code)
    #print new_contents
    #return
    
    g = open(fullpath, 'w')
    g.write(new_contents)
    g.close()
    g = None

# Seems like there should be an easier way to do this?
def strinsert(haystack, idx, insertion):
    if idx == 0:
        return insertion + haystack
    if idx == len(haystack):
        return haystack + insertion
    return haystack[0:idx] + insertion + haystack[idx:]
