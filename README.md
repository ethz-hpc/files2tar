Takes a list of files and splits them into partial lists that when passed to
tar will create archives of a specified size.


# Usage #

## standalone mode ##
Feed it a list of files and you get one or more tar archives.

```shell
# where to store files
out=~/tmp/files2tar

# create input file lists and tar archive and verify result
find /tmp -type f | files2tar --tar-size 1M --no-archive example $out
```

## batch usage ##
Feed it a list of files and you get one or more file lists for further processing.
e.g. for submiting to a batch system where archives are created in parallel.

```shell
# where to store files
out=~/tmp/files2tar

# create input file lists
find /tmp -type f | files2tar --tar-size 1M --no-archive example $out

# create tar archives
for list in $out/*.files; do
   archive="${list%*.files}.tar"
   tar --create --verbose \
      --directory / \
      --files-from "$list" \
      --index-file "${archive}.index" \
      -f "$archive"
done

# verify created archives against the file system
for archive in $out/*.tar; do
   tar --compare \
      --directory / \
      -f "$archive"
done
```
