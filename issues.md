# Issues

Open bugs in the fork (`basedpyright-frozendict`, branch `dev`).

## Notebooks: some show no errors until a cell is edited and saved

**Open (might or might not fix).** Found 2026-11-19, after the server fix for notebook errors (fork 10d4c6ea9).
`scratch/pending.ipynb` shows its errors as soon as it opens; `demonstrations/matplotlib_demonstrations.ipynb`
shows none until a cell is edited and the notebook saved.

**Not the server:** driven with the same messages VS Code sends, the fork server answers the matplotlib notebook's
first diagnostics request in 0.7 s with both errors in its last cell.

**Why (the extension's language client, `vscode-languageclient` 10.1.0, `lib/common/diagnostic.js`):**
1. On a notebook open it pulls each cell only if `visibleDocuments.isVisible(cell.notebook.uri)`, which comes from
   the editor tabs. If the notebook's tab doesn't exist yet, the pull is skipped.
2. When the tab appears later, `visibleDocuments.onOpen` looks the resource up in `workspace.textDocuments`; a
   notebook isn't there, so its cells still aren't pulled.
3. The server's `workspace/diagnostic/refresh` re-pulls visible text documents (cells included), but it's sent
   about 0.5 s after startup, before the tab exists. Nothing pulls again until a cell changes or is saved.

Likely (inferred from timing, not observed in VS Code): the matplotlib notebook holds about 200 KB of saved plot
images, so its tab appears later than that of a small notebook.

**Fix options:**
1. Extension (recommended): when a notebook editor becomes visible (`window.onDidChangeVisibleNotebookEditors`),
   pull its cells' diagnostics. A few lines in the fork's `packages/vscode-pyright`, but `extension.js` has to be
   rebuilt and swapped into the hand-built extension.
2. Server: after a notebook opens, send `workspace/diagnostic/refresh` again a few seconds later. No extension
   rebuild, but it's a timing guess.

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
