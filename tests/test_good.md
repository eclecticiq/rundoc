
Good test
==================================================

This file is used to demonstrate various features and usage of rundoc tool as well as regression test input. All code blocks are supposed to exit with 0 exit code.

### bash blocks

- Code block with bash code and no tags:

```
echo "no tags"
```

- Code block with bash code `bash` tag:

```bash
echo "bash"
```

- Code block with bash code and `bash` and `block-1` tag:

```bash_block-1
echo "bash block-1"
```

- Code block with bash code and `bash` and `block-2` tag:

```bash_block-2
echo "bash block-2"
```

- Code block with bash code and `bash`, `block-1` and `block-2` tag:

```bash_block-1
echo "bash block-1 block-2"
```

### python3 blocks

- Code block with python3 code and `python3` tag:

```python3
print("python3")
```

- Code block with python3 code and `python3` and `block-1` tag:

```python3_block-1
print("python3 block-1")
```

- Code block with python3 code and `python3` and `block-2` tag:

```python3_block-2
print("python3 block-2")
```

- Code block with python3 code and `python3`, `block-1` and `block-2` tag:

```python3_block-1
print("python3 block-1 block-2")
```

