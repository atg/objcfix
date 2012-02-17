import argparse
import os
import sanity
import scanner
import parser
import analyzer
import fixer

def main():
    p = argparse.ArgumentParser()
    p.add_argument('rootdir', metavar='rootdir', nargs='?', default='.', help='the directory to scan (optional: default is the current directory)')
    args = p.parse_args()
    
    root = os.path.abspath(args.rootdir)
    
    sanity.ensure(root)
    
    files = scanner.scan(root)
    defs = list(parser.parse(root, files))
    
    fix_methods = False
    if fix_methods:
        results = analyzer.analyze(root, files, defs)
        fixer.fix_method_declarations(root, defs, results)
    else:
        a2 = analyzer.analyze2(root, files, defs)
        fixer.fix2(root, defs, files, a2)
    
    #fixer.fix_imports(root, defs)

if __name__ == "__main__":
    main()
