Three folders that contain files used for testing sib share operations.

Can be used to test the following things:
---------------------------------------------------------
-diffs
  -add/delete/rename/aggregate/edit
-add/delete/rename/move folders
-merging
-binary file conflicts
-text file conflicts
-updating working directory
-commit given parent


common ancestor contents  #note: binary files don't currently exist.
----------------------
/root
 /empty
 /lipsum.txt
 /folder 1
  /lipsum.txt (identical to other lipsum)
  /folder 2


child A contents  #note: binary files don't currently exist.
----------------------
/root
 /lipsum.txt  (removed a line)
 /folder 1
  /lipsum.txt (identical to other lipsum)
  /folder 2
  /folder 3


child B contents  #note: binary files don't currently exist.
----------------------
/root
 /empty
 /lipsum.txt (added and replaced a line)
 /folder 1
  /lipsum.txt (identical to other lipsum)
  /folder 2
   /folder 4
    /lipsum_rename_reloc.txt (identical to other lipsum)


Correct merged state
----------------------
/root
 /lipsum.txt (removed, added, and replaced a line)
 /folder 1
  /lipsum.txt (identical to other lipsum)
  /folder 3  
  /folder 2
   /folder 4
    /lipsum_rename_reloc.txt (identical to other lipsum)
