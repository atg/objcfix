import os
import itertools
from itertools import chain
import re
import fixer

def flatten(listOfLists):
    return chain.from_iterable(listOfLists)

def ident(x):
    return x.replace('IDENT', '[a-zA-Z_][a-zA-Z0-9_]*')

# @interface regex
interface_re = re.compile(ident(r'@interface\s+(IDENT)\s*(\:\s*(IDENT)(<(IDENT)>)?|\(\s*(IDENT)\s*\)|\(\))([\s\S]+?)@end(\b|$)'), re.MULTILINE) # Do people really define their own base classes?

# @implementation regex
implementation_re = re.compile(ident(r'@implementation\s+(IDENT)\s*((\(\s*(IDENT)\s*\)|\(\))?)([\s\S]+?)@end(\b|$)'), re.MULTILINE)

# #import/#include regex
import_re = re.compile(r'\s*#\s*(import|include)\s*["<]([^">\n]+)[">]', re.MULTILINE)

# @class regex
class_re = re.compile(ident(r'@class\s*((IDENT)(\s*,\s*IDENT)*)\s*;'), re.MULTILINE)

# Method definition/declaration regex
method_re = r'^\s*([+\-][a-zA-Z0-9&$:()^*\[\]<>\s]+)'
method_def_re = re.compile(method_re + r'\{', re.MULTILINE)
method_dec_re = re.compile(method_re + r';', re.MULTILINE)

# Message send regex
message_re = re.compile(r'...', re.MULTILINE)

# Signature regex

# - (void) foo :a bar:b baz:c ;
sig_re = re.compile(ident(r'IDENT\:'))
# - (void) foo ;
basic_sig_re = re.compile(ident(r'(IDENT)\s*$'))

def parse(root, files):
    return chain(
        flatten(parsefile(root, f, False) for f in files["imp_paths"]),
        flatten(parsefile(root, f, True) for f in files["header_paths"])
    )

def find_uses(root, subpath, symbol_names):
    # Attempt to read the file
    try:
        path = os.path.join(root, subpath)
        contents = open(path, 'r').read()
        if not contents:
            return set()
    except Exception:
        return set()
    
    # Make our regex
    r = re.compile(r'(^|[^\w\d])(%s)($|[^\w\d])' % ('|'.join(map(re.escape, symbol_names))))
    
    return set(x[1] for x in r.findall(contents))

def find_includes(root, subpath):
    # Attempt to read the file
    try:
        path = os.path.join(root, subpath)
        contents = open(path, 'r').read()
        if not contents:
            return {'#import':[], '@class':[]}
    except Exception:
        return {'#import':[], '@class':[]}
    
    imports = import_re.findall(contents)
    classes = class_re.findall(contents)
    
    at_class_lines_gen = (fixer.stripsplit(at_class_line[0], ',') for at_class_line in classes)
    at_class_lines = sum(at_class_lines_gen, [])
    
    return {
        '#import': [x[1] for x in imports],
        '@class': at_class_lines,
    }
    

def parsefile(root, subpath, isheader):    
    # Attempt to read the file
    try:
        path = os.path.join(root, subpath)
        contents = open(path, 'r').read()
        if not contents:
            return []
    except Exception:
        return []
    
    defs = []
    
    # If this is not a header, find all @implementations
    if not isheader:
        imps = re.findall(implementation_re, contents)
        for imp in imps:
            impname = imp[0]
            imprawkind = imp[1]
            if imprawkind == '':
                impkind = ''
            elif imprawkind == '()':
                impkind = '()'
            else:
                impkind = imp[3] 
            
            impbody = imp[4]            
            defs.append(parseimp(subpath, impname, impkind, impbody))
    
    # Find any interfaces
    intfs = re.findall(interface_re, contents)
    for intf in intfs:
        intfname = intf[0]
        intfrawkind = intf[1].rstrip()
        intfbody = intf[6]
        defs.append(parseinterface(subpath, intfname, intfrawkind, intfbody))
    
    return defs

## TODO
## Handle categories differently to classes
## Categories should have a name of 'ClassName (CategoryName)'
## Add a new basename key that's just for ClassName

def parseimp(subpath, name, kind, body):
    # Find methods in body
    matches = re.findall(method_def_re, body)
    parsedmethods = []
    if matches:
        parsedmethods = [parsemeth(meth) for meth in matches]
    
    subtype = 'normal'
    category_name = ''
    if kind == '':
        pass
    elif kind == '()':
        subtype = 'extension'
    else:
        subtype = 'category'
        category_name = kind
    
    fullname = name
    if subtype == 'category':
        fullname = '%s (%s)' % (name, category_name)
    
    return {
        'type': '@implementation',
        'basename': name,
        'name': fullname,
        'methods': parsedmethods,
        'kind': kind,
        'subtype': subtype,
        'category_name': category_name,
        'selectors': set(selector_from_signature(sig) for sig in parsedmethods),
        'subpath': subpath,
        'body': body,
        # synthesizes: synthesizes
    }

def parseinterface(subpath, name, kind, body):
    # Find methods in body
    matches = re.findall(method_dec_re, body)
    parsedmethods = []
    if matches:
        parsedmethods = [parsemeth(meth) for meth in matches]
    
    subtype = 'normal'
    category_name = ''
    superclass_name = ''
    if not kind:
        pass
    elif kind[0] == '(':
        subtype = 'category'
        category_name = kind[1:-1].strip()
        if not category_name:
            subtype = 'extension'
    elif kind[0] == ':':
        superclass_name = kind[1:].strip()
    
    fullname = name
    if subtype == 'category':
        fullname = '%s (%s)' % (name, category_name)
    
    return {
        'type': '@interface',
        'basename': name,
        'name': fullname,
        'methods': parsedmethods,
        'kind': kind,
        
        'subtype': subtype,
        'category_name': category_name,
        'superclass_name': superclass_name,
        
        'selectors': set(selector_from_signature(sig) for sig in parsedmethods),
        'subpath': subpath,
        'body': body,
        # synthesizes: synthesizes
    }

def parsemeth(methgroup):
    return ' '.join(methgroup.rstrip().split())

def selector_from_signature(sig):
    sig = sig.lstrip()
    
    comps = re.findall(sig_re, sig)
    if not comps:
        comps = [re.findall(basic_sig_re, sig)[-1]]
    return (sig[0]) + ''.join(comps)
