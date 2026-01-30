
create a project plan which fixes Google personal space,drive space,list
files.That command isn't working right now.Also add commands to the drive
functionality to be able to get a file,to download a file by name,and then to
upload a file by name and to remove a file by name.

```
google-personal drive list-all-files [--profile <profile>]
google-personal drive list-files [--folder <folder>]
google-personal drive get-file [--folder <folder>] --remote-file <filename> [--local-file <filename>]
google-personal drive put-file [--folder <folder>] --local-file <filename> [--remote-file <filename>]
google-personal drive remove-file [--folder <folder>] --remote-file <filename>
```

- --folder is optional when there is only one folder

- --profile is optiona when there is only one profile

- get-file --local-file is optional, and derived from base name of remote file
  - e.g. `get-file --remote-file 'Recording 3.acc'` will just save this file with that same name.
  - abort/fail if the local file already exists

Update README.md and/or any google-personal cli usage document.
