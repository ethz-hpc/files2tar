Takes a list of files and splits them into partial lists that when passed to
tar will create archives of a specified size.


# Usage #

## standalone mode ##
You feed it list of files and you get one or more tar archives.

```shell
# where to store files
out=~/tmp/files2tar

# create input file lists and tar archive and verify result
find /tmp -type f | python files2tar.py -d --tar-size 1M --no-archive example $out
```

## batch usage ##
You feed it list of files and you get lists of files to further process.
e.g. to submit to a cluster batch system to create archives in parallel.

```shell
# where to store files
out=~/tmp/files2tar

# create input file lists
find /tmp -type f | python files2tar.py -d --tar-size 1M --no-archive example $out

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
