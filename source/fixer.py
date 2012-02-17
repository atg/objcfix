import parser
import os
import sys
import re

def fix_method_declarations(root, defs, results):
    p = raw_input('Add method declarations to header files? (y/n)  ')
    if p.lower() != 'y':
        print("Aborting.")
        sys.exit(1)
    
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

def sequencize(en):
    d = {}
    for v in en:
        if v['name'] in d:
            d[v['name']].append(v)
        else:
            d[v['name']] = [v]
    return d

def fix2(root, defs, files, a2):
    
    defmap = sequencize(defs)
    for f in a2['header_files'] | a2['imp_files']:
        print f
        # We need an @class for classes
        f_uses = a2['uses'][f]
        
        is_header = f in a2['header_files']
        
        atclasslines = []
        importlines = []
        
        for u in f_uses:
            for d in defmap[u]:
                if d['type'] == '@interface' and d['subtype'] == 'normal':
                    if is_header:
                        atclasslines.append('@class %s;' % d['basename'])
                    else:                    
                        importlines.append('#import "%s"' % os.path.split(d['subpath'])[1])
                elif d['subpath'] in a2['header_files'] and d['type'] in set(['struct', 'union', 'enum', 'const', 'variable', 'typedef']):
                    importlines.append('#import "%s"' % os.path.split(d['subpath'])[1])
        
        if not importlines and not atclasslines:
            continue
        
        # We put import lines after the *first* block of import/include lines
        
        # Get the full code of the file
        fullpath = os.path.join(root, f)
        fx = open(fullpath, 'r')
        contents = fx.read()
        fx.close()
        f = None
        
        importblock_re = r'(\s*(%s))+' % (parser.import_re.pattern)
        #print importblock_re
        mo1 = re.compile(importblock_re).search(contents)
        #print mo1
        #print mo1.end()
        #print 'GROUP:'
        #print mo1.group()
        #print importlines
        new_contents = contents
        if mo1:
            new_contents = strinsert(new_contents, mo1.end(), '\n' + '\n'.join(importlines) + '\n')
        
        classblock_re = r'(\s*(%s)|\s*(%s))+' % (parser.import_re.pattern, parser.class_re.pattern)
        mo2 = re.compile(classblock_re).search(new_contents)
        if mo2:
            new_contents = strinsert(new_contents, mo2.end(), '\n' + '\n'.join(atclasslines) + '\n')
        
        if not mo1 and not mo2:
            continue
        
        print new_contents
        
        g = open(fullpath, 'w')
        g.write(new_contents)
        g.close()
        g = None

        
        
        
        
    
def fix_imports(root, defs):
    # For each file, build up a list of classes which it uses
    
    needs_class_dec = {}
    needs_import_line = {}
        
    for d in defs:
        if not d['found_classes'] or not len(d['found_classes']):
            continue
        if d['type'] == '@interface':
            if d['subpath'] not in needs_class_dec:
                needs_class_dec[d['subpath']] = set()
            needs_class_dec[d['subpath']].update(d['found_classes'])
        
        if d['type'] == '@implementation':
            if d['subpath'] not in needs_import_line:
                needs_import_line[d['subpath']] = set()
            needs_import_line[d['subpath']].update(d['found_classes'])
    
    for subpath in needs_class_dec:
        if len(needs_class_dec[subpath]) == 0:
            continue
        
        # Load this file off the disk
        fullpath = os.path.join(root, subpath)
        f = open(fullpath, 'r')
        original_contents = f.read()
        f.close()
        f = None

        # Does this have an #import or @class line?
        at_class_lines = re.findall(parser.class_re, original_contents)
        at_class_lines_gen = (stripsplit(at_class_line[0], ',') for at_class_line in at_class_lines)
        at_class_lines = sum(at_class_lines_gen, [])
        
        import_lines = [t[1] for t in re.findall(parser.import_re, original_contents)]
        
        found_classes = needs_class_dec[subpath]
        
        needs_at_class = []
        print "-- " + subpath
        for cl in found_classes:
            accept = True
            for import_line in import_lines:
                if cl in import_line:
                    accept = False
                    break
            for at_class_line in at_class_lines:
                if cl in at_class_line:
                    accept = False
                    break
            if accept:
                needs_at_class.append(cl)
                print '@class ' + cl + ';'
        
        print import_lines
        print at_class_lines
    
    #for subpath in needs_class_dec:
    #    print subpath
    #    print needs_class_dec[subpath]

def declare_methods(root, methods, main_interface):
    
    # Get the full code of the original interface
    original_code = main_interface['body']
    
    # Find a method to insert after (or else find the last } )
    #   1. First try to find the last ';'
    #   2. Then try to find the last '}'
    #   3. Then just insert at the end
    
    insert_idx = max(original_code.rfind(';'), original_code.rfind('}'))
    
    if insert_idx == -1:
        insert_idx = len(original_code)
    else:
        insert_idx += 1
    
    # Insert the methods
    new_methods = '\n\n' + '\n'.join(meth + ';' for meth in methods) + '\n'
    new_code = strinsert(original_code, insert_idx, new_methods)
        
    # Get the full code of the file
    fullpath = os.path.join(root, main_interface['subpath'])
    f = open(fullpath, 'r')
    contents = f.read()
    f.close()
    f = None
    
    # Replace the original interface with the new one
    new_contents = contents.replace(original_code, new_code)
        
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

def stripsplit(s, by):
    v = [x.strip() for x in s.strip().split(by)]
    return [x for x in v if x]

