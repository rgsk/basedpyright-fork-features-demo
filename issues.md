# Issues

Open bugs in the fork (`basedpyright-frozendict`, branch `dev`).

## SimpleNamespace: a global's nested namespaces still report missing attributes

**Fixed 2026-11-14 (option 1):** nested dicts, ModuleDicts and namespaces of a global read in a function are
marked too (`markOuterScopeEntries`), and hover labels a namespace attribute `(variable)`.

Found 2026-11-14. A function reading a global namespace doesn't report missing attributes (code that runs before
the call may add them, as with globals for dicts and ModuleDict). But the namespaces inside it still do:

```python
from types import SimpleNamespace as namespace

app = namespace(name='shop', db=namespace(host='localhost', port=5432, user='admin'))

def check() -> str:
    app.sssss        # no error: app's attributes are marked as an outer scope's
    db = app.db
    return db.users  # error: Cannot access attribute "users" (app.db.users too)
```

**Why:** `getDictTypeInFunction` (`typeEvaluator.ts`) marks only the top-level type with
`ClassType.cloneForOuterScopeEntries`; the nested namespace in `app`'s entries is the stored one, unmarked.

**Fix options (undecided):**
1. Mark nested namespaces too, so `db.users` isn't an error either (one rule for dicts, ModuleDict and
   namespaces). Recommended.
2. Drop the outer-scope exception for namespaces, so `app.sssss` is an error too (more typos caught, but a false
   error when unseen setup code adds an attribute).

**Also:** hover on the missing attribute says `(function) users: Unknown`; it shouldn't be labelled a function.

## SimpleNamespace: a return annotation erases the shape

**Fixed 2026-11-14:** `-> SimpleNamespace` keeps the shape the body returns.

Found 2026-11-14. A dict or frozendict return annotation keeps the shape the body returns (fork 4b2381bbf), but a
`SimpleNamespace` one doesn't:

```python
from types import SimpleNamespace as namespace

def f() -> namespace:
    return namespace(name='rahul')

u = f()   # SimpleNamespace, wanted SimpleNamespace[{name: str}]

def g() -> dict:
    return {'name': 'rahul'}

d = g()   # dict[{'name': str}]
```

**Why:** `getShapedReturnTypeOfDict` (`typeEvaluator.ts`) only handles `dict` and `frozendict` annotations.

**Fix:** accept `SimpleNamespace` there too: when every return gives a namespace with the same attributes, callers
get that shape. There's no value type to bound, so the attribute types are the inferred ones (like a bare
`-> dict`). Returns with different attributes keep the plain `SimpleNamespace`.
