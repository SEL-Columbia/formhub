// spanDir - a directory traversal function for
// Rhino JavaScript
// Copyright 2010 by James K. Lawless
// See MIT/X11 license at 
// http://www.mailsend-online.com/wp/license.php

importPackage(java.io);

// spanDir() accepts two parameters
// The first is a string representing a directory path
// The second is a closure that accepts a parameter of type
// java.io.File
function spanDir(dir,dirHandler) {
    var lst=new File(dir).listFiles().sort(),
        i;

    for(i=0;i<lst.length;i++) {
        // If it's a directory, recursive call spanDir()
        // so that we end up doing a scan of
        // the directory tree
        if(lst[i].isDirectory()) {
            spanDir(lst[i].getCanonicalPath(),dirHandler);
        }
        // Pass the File object to the handler that
        // the caller has specified regardless of whether
        // the File object is a directory.
        dirHandler(lst[i].getCanonicalPath());
    }
}
