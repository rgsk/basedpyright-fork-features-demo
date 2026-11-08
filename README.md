# latest-python-features

*Last updated: 2026-11-08 (fork `dev` at 174a90fbd).*

A Python 3.15 playground. Its main use so far is a local basedpyright fork that gives each key of a dict or a
`frozendict` (PEP 814), and of PyTorch's `nn.ModuleDict`, its own type, inferred from how the dict is built.

**The rule for the fork: code must never need it.** It only infers; it adds no new syntax. Other checkers see plain
`dict[str, ...]` and `frozendict[str, ...]` types and lose only precision. To declare a shape, use a class
(`TypedDict`, `NamedTuple`, `dataclass`), which every checker understands.

| Demo file | What it shows | Intended errors |
|---|---|---|
| [frozendict_demonstrations.py](frozendict_demonstrations.py) | frozendicts: exact shapes, typo'd keys are errors | 2 |
| [dict_demonstrations.py](dict_demonstrations.py) | plain dicts remember their keys; writes update them | 2 |

Each `reveal_type(...)` line has the checker's result in a comment, each intended error is marked, and both files
run as-is.

## frozendict with per-key types

Stock basedpyright types `frozendict(name='rahul', age=27)` as `frozendict[str, str | int]`, so every key reads as
`str | int`. A frozendict can't change after it's built, so the fork records each key's own type (its *shape*) and
uses it everywhere. The keys are exact: a frozendict has exactly the keys in its shape.

| Feature | Example | Section in `frozendict_demonstrations.py` |
|---|---|---|
| Per-key types | `user['age']` is `int`, `user['name']` is `str` | Works today |
| Typo'd keys are errors | `user['nme']`: *Could not access item in frozendict* | Works today |
| Key completion | typing `user[` offers `"name"`, `"age"` | Works today |
| Key hover | hovering `'name'` in `user['name']` shows `(key) name: str`, as for a TypedDict key | Works today |
| Go to definition on keys | ctrl+click `'name'` in `user['name']` jumps to where the key was added (`name=`, `{'name': ...}`, `fromkeys`, either side of a `\|`) | (try it in the editor) |
| Keys coloured as properties | known keys get their own colour (see Setup); a typo'd key stays string-coloured | (try it in the editor) |
| Shapes print as types | errors, `reveal_type`: `frozendict[{'name': str, 'age': int}]`, also nested; hover shows one key per line | Works today |
| Inferred return types keep the shape | `def make(): return frozendict(...)` | Works today |
| Merging keeps the shape | `a \| b`, `a \| {...}`, `a \|= b`, `frozendict(a, k=v)`, `frozendict({**a, ...})`, `frozendict(**a, ...)` | Merging keeps the shape |
| `.get()` and `.copy()` | `.get('age')` is `int`; `.get('nme')` is `None` (no error); `.copy()` keeps the shape | .get() and .copy() |
| `**` unpacking | `greet(**user)` checks each key against its own parameter, also against `**kwargs: Unpack[TD]` | Like a TypedDict |
| `match` patterns | `case {'age': v}` gives `v: int` | Like a TypedDict |
| Narrowing by key | `if 'radius' in shape:` narrows a union of shapes | Like a TypedDict |
| `fromkeys` | `frozendict.fromkeys(['lr', 'momentum'], 0.0)` is `{'lr': float, 'momentum': float}` | fromkeys |

A declared type is what callers see: `def f() -> frozendict[str, int]` has no shape at its call sites.

### Python < 3.15: the `frozendict` package

Before 3.15 there's no built-in `frozendict`, but the [frozendict](https://pypi.org/project/frozendict/) package on
PyPI provides one (`from frozendict import frozendict`). The fork treats it like the built-in, so everything above
works with it.

Only what the built-in also has gets per-key types, so moving to 3.15 later just means dropping the import. The
package's own `.set()` and `.delete()` keep its stub's plain types; use `user | {'key': value}` instead of `.set()`.
`~/Documents/codes/ml/dream-robot` (Python 3.14) uses it: see `rough/scratch.py` there.

## dict: the keys the checker has seen

A dict can change, so its shape can't be exact. The fork uses one rule:

> A dict literal remembers its keys. Writes in the same function update that memory. A function reading a global
> dict sees the keys of the code (and notebook cells) above it. Wherever the checker can't follow the dict, it is a
> plain `dict[str, ...]`, as today.

| Feature | Example | Section in `dict_demonstrations.py` |
|---|---|---|
| Per-key types, also nested | `user['age']` is `int`, `user['details']['sex']` is `str`; `dict(lr=1e-3)` too | A dict literal remembers its keys |
| Shapes print as types | hover on `user`: `dict[{'name': str, 'age': int}]`, one key per line | A dict literal remembers its keys |
| Writes update the shape | `user['name'] = 2` changes the key's type, `user['joker'] = ...` adds a key, `del` removes one | Writes in the same function |
| Methods with literal keys | `.update(k=v)`, `.update({...})`, `\|=`, `.pop('k')`, `.setdefault(...)`, `.clear()`; `.get()`, `.copy()`, `{**d}`, `d \| {...}` keep it | Writes in the same function |
| `.update()` works like `\|=` | `user = {'name': 'rahul'}; user.update({'b': 20})` is `dict[{'name': str, 'b': int}]`, no error (stock pyright rejects the `int`); a declared `user: dict[str, str]` keeps the error | (try it in the editor) |
| Dict comprehensions over known keys | `{s: f(s) for s in rows}` (also `rows.keys()`, `k, v in rows.items()`, `['a', 'b']`, `[('a', x), ('b', y)]`) has `rows`' keys, each with the value's type; with an `if` clause it's plain | A dict comprehension over known keys |
| Branches | after an `if`, a key keeps every type it can have; a key set in one branch only is forgotten | Branches |
| Keys the checker can't read | `scores[subject] = 100` forgets every key | Unknown keys |
| Inferred return types keep the shape | `def make(): d = {...}; ...; return d` | Inferred return types |
| Across notebook cells | a later cell sees the keys at the end of the cells before it, writes in between included (cells run in order) | (try it in a notebook) |
| Globals read in a function | have the keys of the code and cells above the function (read top to bottom, as a notebook is: an assignment below doesn't count) | A global read in a function |
| Plain where it can't follow | attributes (`self.cfg`), dicts inside lists or tuples | Where the checker can't follow |
| Filled key by key | `d = {}; d['env'] = 22` is `dict[{'env': int}]` (a declared `d: dict[str, int] = {}` keeps its type) | (try it in the editor) |
| Key completion | typing `user[` offers the keys, also for `make()[` | (try it in the editor) |
| Go to definition on keys | ctrl+click `'sex'` in `prb['sex']` jumps to where the key was first added (literal, keyword, adding write, `setdefault`, `\|`), also across notebook cells | (try it in the editor) |
| Keys coloured as properties | known keys (also TypedDict keys) are coloured like attributes; a typo'd key stays string-coloured | (try it in the editor) |

It never adds errors by itself: an unknown key reads as today's type, and writes are checked against the dict's
value type, as today. The only new errors come from precise reads, like `user['age'].upper()` on an `int`.

**Known hole**, the same one pyright accepts for `d['k'] = v` narrowing: a call that changes the dict, like
`rename(user)` or `user.update(other)` through an alias, isn't seen, so the shape can be stale.

## PyTorch's nn.ModuleDict

Stock basedpyright types every read of a `ModuleDict` as `Module`, because that's what its `__getitem__` declares.
The fork gives a `ModuleDict` built from a dict with literal keys the same per-key shape:

```python
core = nn.ModuleDict(dict(tau=nn.Linear(1, D), body=nn.TransformerEncoder(layer, num_layers=4))).to(dev)
core['body']   # TransformerEncoder
core['bdy']    # error: Could not access item in ModuleDict
```

| Feature | Example |
|---|---|
| Built from a dict | `nn.ModuleDict(dict(k=v, ...))`, `nn.ModuleDict({'k': v, ...})`, or a dict variable that has a shape |
| Shapes print as types | `ModuleDict[{'tau': Linear, 'body': TransformerEncoder}]` |
| Methods that return self keep it | `.to(...)`, `.cuda()`, `.cpu()`, `.train()`, `.eval()`, `.requires_grad_()` and chains of them (torch declares them `-> Self`), also `copy.deepcopy(core)` |
| Typo'd keys are errors | `core['bdy']`; a key that isn't a literal reads as `Module`, as today |
| `.update()` adds keys | `enc.update(dict(film=nn.Linear(8, 256)))` makes `enc['film']` a `Linear` (its only way to add keys: no `\|=`) |
| Other writes make it plain | `core['x'] = ...`, `del core['x']`, `.update()` with unknown keys, `.pop()`, `.clear()`, `.add_module()`, `.register_module()`: from there on it's a plain `ModuleDict` and reads are `Module` |
| Like a dict elsewhere | key completion, key hover, inferred return types, notebook cells and globals read in a function work; attributes (`self.core`) are plain |

Two rules differ from a dict's, so that a missing key can be an error:

- **Any write the checker sees makes it plain** (except `.update()` with known keys), instead of updating the shape. With an updated shape, a key added in
  only one branch of an `if` would be forgotten, and reading it afterwards would be a false error. Two branches that
  build ModuleDicts with different keys make it plain too.
- **Inside a function, a missing key isn't an error.** Code that runs before the call may have added it, so
  `enc['not_yet']` in a function reads as `Module`, as today.
- **Known hole:** a key added where the checker can't see it (through an alias, `add_head(core)`, or `core.x = ...`)
  is reported as missing although it works at runtime. With a dict, the same hole only leaves the shape stale.

Only `torch.nn.ModuleDict` itself gets a shape, not its subclasses. `nn.ParameterDict` is left alone: its stub takes
and returns `Any`, and at runtime it wraps plain tensors in `Parameter`, so the argument types would be wrong.
`~/Documents/codes/ml/dream-robot/rough/dino_parts.py` uses it (`student`, and `teacher` made from it with
`copy.deepcopy(...).requires_grad_(False)`).

## Design decisions

- **No shape annotations.** `frozendict[{'name': str}]` and `dict[{'name': str}]` are display only; in an
  annotation they're errors, as in every other checker. Annotations would make code require the fork. The draft
  inline `TypedDict[{...}]` (PEP 764) also raises `TypeError` at runtime on 3.15 wherever it's evaluated. Shapes
  that cross functions are declared with a class instead.
- **The checker reports an error only where the code would fail at runtime.** `user['nme']` on a frozendict raises
  `KeyError`, so it's an error. `user.get('nme')` returns `None`, so it isn't; its type is exactly `None`, and
  misuse such as `.upper()` is reported where it would actually fail.
- **A frozendict's keys are exact, and always present.** `'age': int | None` means the key is there and its value
  may be `None`. There's no `NotRequired`, so `user['key']` is always safe.
- **A frozendict's shape comes only from what it was built with.** Not from a TypedDict (a plain `dict` at runtime,
  so its keys are only a promise) and not from a dict's remembered keys (unseen code may have changed them):
  `frozendict(some_dict)` has no shape. Neither does merging with an unshaped side, or building from
  `(key, value)` pairs.
- **Hover breaks shapes one key per line** (indented, trailing commas, nested shapes indented further), like
  TypeScript's hover; errors, `reveal_type` and completion keep the single-line form. A shape always prints with the
  class's own name (`dict`, `frozendict`), even where a stub spells the type `typing.Dict`.
- **A dict's shape is advisory.** It never restricts what can be assigned to the dict or passed from it, and
  `'k' in d` doesn't narrow it.
- **Rejected:** `dict[{...}]`/`frozendict[{...}]` annotations (dropped 2026-11-05), `frozendict[SomeTypedDict]`,
  a `FrozenDict` base-class package (a frozen dataclass covers that), and a `class _(TypedDict)` block in hover.
- **Later, maybe:** a `sealeddict` package, a dict subclass whose keys can't be added or removed (checked at
  runtime too), for TS-style errors on writes. Parked ideas and plans are in [roadmap.md](roadmap.md).

## Known gaps

- **Notebooks:** VS Code shows no basedpyright diagnostics in `.ipynb` files (an upstream pull-diagnostics issue;
  the server computes them). Hover and completion work. Use `.py` files to see errors.
- **Literals in tuples:** `frozendict(size=(1, 2))` keeps `tuple[Literal[1], Literal[2]]`, because stock pyright
  solves the value type that way for keyword arguments. A dict display `frozendict({'size': (1, 2)})` gives
  `tuple[int, int]`. (`dict(size=(1, 2))` is widened to `tuple[int, int]`.)
- **Standard mode:** with `typeCheckingMode = "standard"` (this project), `strictDictionaryInference` is off, so
  stock basedpyright types a dict literal with mixed values as `dict[str, Unknown]`. The fork's shapes still give
  each key its type; the dict's value type stays `Unknown`, so writes aren't checked.

## Setup

- **The fork:** `../basedpyright-frozendict` (local only). All work is on one branch, `dev`, on top of
  basedpyright `main`; commit there and build from it. The history has one commit per step (frozendict
  support, the PyPI package, dict keys, dropping the annotations, notebook cells, multi-line hover, `{}` shapes,
  key colouring, go-to-definition on keys, the VS Code switch, `nn.ModuleDict`, ...).

  Rebuild with `npx pnpm@11.21.0 run build:cli:dev` in the fork, then restart the server
  (*BasedPyright: Restart Server*) or reload VS Code. Run tests one worker at a time (`jest --runInBand`); a full
  parallel run can take the machine down.
- **VS Code runs the fork in every project** through one user setting:

  ```jsonc
  "basedpyright.fork.enabled": true,   // false: stock basedpyright
  "basedpyright.fork.serverPath": "~/Documents/codes/projects/basedpyright-frozendict/packages/pyright/langserver.index.js",
  ```

  The switch comes from a hand-built VSIX installed in place of the marketplace extension
  (`../basedpyright-frozendict/packages/vscode-pyright/basedpyright-fork.vsix`): stock 1.40.2, including its
  stock server, with the fork's `extension.js`. Changing the setting asks to reload the window. It takes
  precedence over `importStrategy`; the per-project `.venv/bin/basedpyright-langserver` wrappers it replaced
  (here, rl, dream-robot) were removed. Turn off auto-update for the extension: a marketplace update replaces
  the VSIX and the switch with it.
  The usual window is the `../frozendict-dev.code-workspace` workspace (this project plus the fork).
- **Key colour:** the fork marks dict keys as semantic tokens `property` with a `key` modifier (plus `readonly`
  for frozendict and ReadOnly TypedDict keys). The colour is in user settings,
  `editor.semanticTokenColorCustomizations`: `property.key:python` and `property.key.readonly:python`, both
  `#C9848E`. After a reload, a notebook may need one edit before its keys are coloured.
- **Comparing against stock basedpyright:** set `basedpyright.fork.enabled` to `false`, or open
  `../playground-stock` in a second window: basedpyright 1.40.2 from PyPI, symlinks to both demo files, and
  `basedpyright.fork.enabled: false` in its `.vscode/settings.json`.
- **Checking from the shell:**
  `node ../basedpyright-frozendict/packages/pyright/index.js -p pyproject.toml frozendict_demonstrations.py dict_demonstrations.py`
