import argparse
import os
import scanner

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rootdir', metavar='rootdir', nargs='?', default='.', help='the directory to scan (optional: default is the current directory)')
    args = parser.parse_args()
    
    root = os.path.abspath(args.rootdir)
    
    scanner.scan(root)

if __name__ == "__main__":
    main()
