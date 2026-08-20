# Getting started

## Install

```bash
pip install dhidb
```

## Connect to public QAS storage

Public reads use unsigned S3 requests. No access key is required.

```python
from dhidb import DHIProvider

db = DHIProvider()
print(db.years)
print(db.variables)
db.close()
```

The provider uses the public endpoint and array defaults, so Python needs no
connection arguments:

```python
from dhidb import DHIProvider

with DHIProvider() as db:
    print(db.metadata)
```


## Query safety

The default client refuses a request containing more than 50 million
space-time cells. This protects laptops from accidentally materializing a
global array. Raise the limit deliberately when appropriate:

```python
db = DHIProvider(max_cells=100_000_000)
```
