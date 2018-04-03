
Good test
==================================================

This file is used to demonstrate various features and usage of rundoc tool as well as regression test input. All code blocks are supposed to exit with 0 exit code.

### environments and secrets

```env
r_env_0=0
r_env_1=1
```

```env#block-1
r_env_2=2
r_env_3=3
```

```env#block-2
r_env_4=4
r_env_5=5
```

```environment
r_env_6=6
r_env_7=7
```

```environment#block-1
r_env_8=8
r_env_9=9
```

```environment#block-2
r_env_10=10
r_env_11=11
```

```environ#block-1#block-2
r_env_12=12
r_env_13=13
```

```secret
r_sec_0=0
r_sec_1=1
```

```secrets
r_sec_2=2
r_sec_3=3
```

```secret#block-1
r_sec_4=4
r_sec_5=5
```

```secrets#block-2
r_sec_6=6
r_sec_7=7
```

```secret#block-1#block-2
r_sec_8=8
r_sec_9=9
```

### bash blocks

- Code block with bash code and no tags:

```
echo "no tags"
eval 'echo $r_env_{0..13}'
eval 'echo $r_sec_{0..9}'
```

- Code block with bash code `bash` tag:

```bash
echo "bash"
eval 'echo $r_env_{0..13}'
eval 'echo $r_sec_{0..9}'
```

- Code block with bash code and `bash` and `block-1` tag:

```bash#block-1
echo "bash block-1"
eval 'echo $r_env_{0..13}'
eval 'echo $r_sec_{0..9}'
```

- Code block with bash code and `bash` and `block-2` tag:

```bash#block-2
echo "bash block-2"
eval 'echo $r_env_{0..13}'
eval 'echo $r_sec_{0..9}'
```

- Code block with bash code and `bash`, `block-1` and `block-2` tag:

```bash#block-1#block-2
echo "bash block-1 block-2"
eval 'echo $r_env_{0..13}'
eval 'echo $r_sec_{0..9}'
```

### python3 blocks

- Code block with python3 code and `python3` tag:

```python3
import os
from contextlib import suppress
print("python3")
for x in range(0,14):
    with suppress(KeyError):
        print(os.environ['r_env_'+str(x)])
for x in range(0,10):
    with suppress(KeyError):
        print(os.environ['r_sec_'+str(x)])
```

- Code block with python3 code and `python3` and `block-1` tag:

```python3#block-1
import os
from contextlib import suppress
print("python3 block-1")
for x in range(0,14):
    with suppress(KeyError):
        print(os.environ['r_env_'+str(x)])
for x in range(0,10):
    with suppress(KeyError):
        print(os.environ['r_sec_'+str(x)])
```

- Code block with python3 code and `python3` and `block-2` tag:

```python3#block-2
import os
from contextlib import suppress
print("python3 block-2")
for x in range(0,14):
    with suppress(KeyError):
        print(os.environ['r_env_'+str(x)])
for x in range(0,10):
    with suppress(KeyError):
        print(os.environ['r_sec_'+str(x)])
```

- Code block with python3 code and `python3`, `block-1` and `block-2` tag:

```python3#block-1#block-2
import os
from contextlib import suppress
print("python3 block-1 block-2")
for x in range(0,14):
    with suppress(KeyError):
        print(os.environ['r_env_'+str(x)])
for x in range(0,10):
    with suppress(KeyError):
        print(os.environ['r_sec_'+str(x)])
```

