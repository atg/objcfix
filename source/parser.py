import os
import itertools
from itertools import chain
import re

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
class_re = re.compile(r'@class\s*((IDENT)(\s*,\s*IDENT)*)\s*;', re.MULTILINE)

# Method definition/declaration regex
method_re = r'^\s*([+\-][a-zA-Z0-9&$:()^*\[\]<>\s]+)'
method_def_re = re.compile(method_re + r'\{', re.MULTILINE)
method_dec_re = re.compile(method_re + r';', re.MULTILINE)

# Message send regex
message_re = re.compile(r'...', re.MULTILINE)

def parse(root, files):
    return chain(
        flatten(parsefile(root, f, False) for f in files["imp_paths"]),
        flatten(parsefile(root, f, True) for f in files["header_paths"])
    )

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
            # print imp
            impname = imp[0]
            imprawkind = imp[1]
            if imprawkind == '':
                impkind = ''
            elif imprawkind == '()':
                impkind = '()'
            else:
                impkind = imp[3] 
            
            impbody = imp[4]            
            defs.extend(parseimp(impname, impkind, impbody))
    
    #print defs
    
    return defs

def parseimp(name, kind, body):
    # Find methods in body
    matches = re.findall(method_def_re, body)
    #print matches
    if not matches:
        return []
    return [parsemeth(meth) for meth in matches]

def parsemeth(methgroup):
    return methgroup.rstrip()

    
    
