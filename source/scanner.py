import os

# Some of these were added purely for selfish reasons and are specific to Chocolat
INVALID_DIR_NAMES = set(['.git', '.svn', 'build', 'git_ignored', 'Resources', 'boost'])
INVALID_DIR_EXTS = set(['.xcodeproj', '.xcode', '.lproj', '.app'])
HEADER_EXTS = set(['.h', '.hpp', '.hh'])
IMP_EXTS = set(['.m', '.M', '.mm'])

def isvaliddir(d):
    if d in INVALID_DIR_NAMES:
        return False
    ext = os.path.splitext(d)[1]
    if ext in INVALID_DIR_EXTS:
        return False
    return True

def scan(root):
    print 'scanner:' + root
    
    headerfiles = set()
    impfiles = set()
    
    # We want to get a list of files
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if isvaliddir(d)]
        
        for f in files:
            path = os.path.join(r, f)
            ext = os.path.splitext(path)[1]
            
            if ext not in HEADER_EXTS and ext not in IMP_EXTS:
                # Ignore this
                continue
            
            relpath = os.path.relpath(path, start=root)
            
            if ext in HEADER_EXTS:
                headerfiles.add(relpath)
            elif ext in IMP_EXTS:
                impfiles.add(relpath)
            
            print relpath
    return {
        'header_paths': headerfiles,
        'imp_paths': impfiles,
    }
