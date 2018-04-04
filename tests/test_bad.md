
Bad test
==================================================

This file is used to test the stderr and stdout merging.

```bash
echo "this is good 1"
echo "this is good 2"
echo "this is good 3"
echo "this is good 4"
echo "this is good 5"
echo "this is good 6"
echo "this is good 7"
echo "this is good 8"
echo "this is bad  1" 1>&2
echo "this is bad  2" 1>&2
echo "this is bad  3" 1>&2
echo "this is bad  4" 1>&2
echo "this is bad  5" 1>&2
echo "this is bad  6" 1>&2
echo "this is bad  7" 1>&2
echo "this is bad  8" 1>&2
```

```bash
echo "this is bad  1" 1>&2
echo "this is bad  2" 1>&2
echo "this is bad  3" 1>&2
echo "this is bad  4" 1>&2
echo "this is bad  5" 1>&2
echo "this is bad  6" 1>&2
echo "this is bad  7" 1>&2
echo "this is bad  8" 1>&2
echo "this is good 1"
echo "this is good 2"
echo "this is good 3"
echo "this is good 4"
echo "this is good 5"
echo "this is good 6"
echo "this is good 7"
echo "this is good 8"
```

```bash
echo "this is good 1"
echo "this is good 2"
echo "this is bad  1" 1>&2
echo "this is bad  2" 1>&2
echo "this is good 3"
echo "this is good 4"
echo "this is bad  3" 1>&2
echo "this is good 5"
echo "this is bad  4" 1>&2
echo "this is good 6"
echo "this is bad  5" 1>&2
echo "this is bad  6" 1>&2
echo "this is good 7"
echo "this is good 8"
echo "this is bad  7" 1>&2
echo "this is bad  8" 1>&2
```

```bash
echo "this is bad  1" 1>&2
echo "this is bad  2" 1>&2
echo "this is good 1"
echo "this is good 2"
echo "this is bad  3" 1>&2
echo "this is good 3"
echo "this is bad  4" 1>&2
echo "this is good 4"
echo "this is bad  5" 1>&2
echo "this is bad  6" 1>&2
echo "this is good 5"
echo "this is good 6"
echo "this is bad  7" 1>&2
echo "this is bad  8" 1>&2
echo "this is good 7"
echo "this is good 8"
```

