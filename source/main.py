import argparse
import os
import scanner
import parser
import analyzer

def main():
    p = argparse.ArgumentParser()
    p.add_argument('rootdir', metavar='rootdir', nargs='?', default='.', help='the directory to scan (optional: default is the current directory)')
    args = p.parse_args()
    
    root = os.path.abspath(args.rootdir)
    
    files = scanner.scan(root)
    defs = parser.parse(root, files)
    results = analyzer.analyze(root, files, defs)

if __name__ == "__main__":
    main()
