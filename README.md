# latest-python-features

A Python 3.15 playground. Its main use so far is a local basedpyright fork that gives each key of a dict or a
`frozendict` (PEP 814) its own type, inferred from how the dict is built.

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

> A dict literal remembers its keys. Writes in the same function update that memory. Wherever the checker can't
> follow the dict, it is a plain `dict[str, ...]`, as today.

| Feature | Example | Section in `dict_demonstrations.py` |
|---|---|---|
| Per-key types, also nested | `user['age']` is `int`, `user['details']['sex']` is `str`; `dict(lr=1e-3)` too | A dict literal remembers its keys |
| Shapes print as types | hover on `user`: `dict[{'name': str, 'age': int}]`, one key per line | A dict literal remembers its keys |
| Writes update the shape | `user['name'] = 2` changes the key's type, `user['joker'] = ...` adds a key, `del` removes one | Writes in the same function |
| Methods with literal keys | `.update(k=v)`, `\|=`, `.pop('k')`, `.setdefault(...)`, `.clear()`; `.get()`, `.copy()`, `{**d}`, `d \| {...}` keep it | Writes in the same function |
| Branches | after an `if`, a key keeps every type it can have; a key set in one branch only is forgotten | Branches |
| Keys the checker can't read | `scores[subject] = 100` forgets every key | Unknown keys |
| Inferred return types keep the shape | `def make(): d = {...}; ...; return d` | Inferred return types |
| Across notebook cells | a later cell sees the keys at the end of the cells before it, writes in between included (cells run in order) | (try it in a notebook) |
| Plain where it can't follow | attributes (`self.cfg`), globals read in a function, dicts inside lists or tuples | Where the checker can't follow |
| Key completion | typing `user[` offers the keys, also for `make()[` | (try it in the editor) |

It never adds errors by itself: an unknown key reads as today's type, and writes are checked against the dict's
value type, as today. The only new errors come from precise reads, like `user['age'].upper()` on an `int`.

**Known hole**, the same one pyright accepts for `d['k'] = v` narrowing: a call that changes the dict, like
`rename(user)` or `user.update(other)` through an alias, isn't seen, so the shape can be stale.

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
  runtime too), for TS-style errors on writes.

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
  support, the PyPI package, dict keys, dropping the annotations, notebook cells, multi-line hover, ...).

  Rebuild with `npx pnpm@11.21.0 run build:cli:dev` in the fork, then reload VS Code. Run tests one worker at a
  time (`jest --runInBand`); a full parallel run can take the machine down.
- **VS Code runs the fork** through the wrapper `.venv/bin/basedpyright-langserver` (with
  `basedpyright.importStrategy: fromEnvironment`). Delete the wrapper to go back to the bundled basedpyright.
  The usual window is the `../frozendict-dev.code-workspace` workspace. dream-robot has the same wrapper, with
  its stock script saved next to it as `basedpyright-langserver.stock`. A `uv sync` that reinstalls basedpyright
  overwrites a wrapper.
- **Comparing against stock basedpyright:** open `../playground-stock` in a second window. It has basedpyright
  1.40.2 from PyPI and symlinks to both demo files. (There's one basedpyright server per window, so the two can't
  share a workspace.)
- **Checking from the shell:**
  `node ../basedpyright-frozendict/packages/pyright/index.js -p pyproject.toml frozendict_demonstrations.py dict_demonstrations.py`
