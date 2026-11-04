# latest-python-features

A Python 3.15 playground. Its main use so far is trying out the built-in `frozendict` (PEP 814), along with a
local basedpyright fork that gives each key of a frozendict its own type.

## frozendict with per-key types (basedpyright fork)

Stock basedpyright types `frozendict(name='rahul', age=27)` as `frozendict[str, str | int]`, so every key reads as
`str | int`. A frozendict can't change after it's built, so the fork records each key's own type (its *shape*) and
uses it everywhere.

**Try it:** [demonstrations.py](demonstrations.py). Each `reveal_type(...)` line has the checker's result in a
comment, and the file runs as-is. It has 4 intended errors, each marked in a comment.

### What works

| Status | Feature | Example | Section in `demonstrations.py` |
|---|---|---|---|
| ✅ | Per-key types | `user['age']` is `int`, `user['name']` is `str` | Works today |
| ✅ | Typo'd keys are errors | `user['nme']`: *Could not access item in frozendict* | Works today |
| ✅ | Key completion | typing `user[` offers `"name"`, `"age"` | Works today |
| ✅ | Key hover | hovering `'name'` in `user['name']` shows `(key) name: str`, as for a TypedDict key | Works today |
| ✅ | Shapes print as types | hover, errors, `reveal_type`: `frozendict[{'name': str, 'age': int}]`, also nested (`tuple[frozendict[{...}], int]`) | Works today |
| ✅ | Shapes in annotations | `type User = frozendict[{'name': str, 'age': int}]`, `def load() -> User` | Works today; Declared return types |
| ✅ | Exact keys | assigning to `User` with a missing, extra or wrong-typed key is an error | Works today |
| ✅ | Merging keeps the shape | `a \| b`, `a \| {...}`, `a \|= b`, `frozendict(a, k=v)`, `frozendict({**a, ...})`, `frozendict(**a, ...)` | Merging keeps the shape |
| ✅ | `.get()` and `.copy()` | `.get('age')` is `int`; `.get('nme')` is `None` (no error); `.copy()` keeps the shape | .get() and .copy() |
| ✅ | `fromkeys` | `frozendict.fromkeys(['lr', 'momentum'], 0.0)` is `{'lr': float, 'momentum': float}`; merges into other shapes | fromkeys |
| ✅ | `**` unpacking | `greet(**user)` checks each key against its own parameter, also against `**kwargs: Unpack[TD]` | Like a TypedDict |
| ✅ | `match` patterns | `case {'age': v}` gives `v: int` | Like a TypedDict |
| ✅ | Union narrowing | `if s['kind'] == 'circle':` and `if 'radius' in s:` narrow `Circle \| Square` to `Circle` | Like a TypedDict |
| ✅ | Tagged records | `frozendict(kind='circle', ...)` keeps `Literal['circle']` where a `Circle` is expected | Like a TypedDict |
| ✅ | Completion while building | typing `{` or `(` in `u: User = frozendict(` offers the shape's keys | Like a TypedDict |

### Python < 3.15: the `frozendict` package

Before 3.15 there's no built-in `frozendict`, but the [frozendict](https://pypi.org/project/frozendict/) package on
PyPI provides one (`from frozendict import frozendict`). The fork treats it like the built-in, so everything above
works with it, including `frozendict[{...}]` annotations, which the package accepts at runtime on 3.14.

Only what the built-in also has gets per-key types, so moving to 3.15 later just means dropping the import. The
package's own `.set()` and `.delete()` keep its stub's plain types; use `user | {'key': value}` instead of `.set()`.
`~/Documents/codes/ml/dream-robot` (Python 3.14) uses it: see `rough/scratch.py` there.

### Design decisions

- **Shape notation `frozendict[{'name': str}]`**: square brackets like the rest of typing, with quoted keys. It's
  the only spelling that is valid Python at runtime, and it mirrors the draft inline TypedDict syntax
  (PEP 764, `TypedDict[{'name': str}]`). An unquoted `frozendict[{name: str}]` raises `NameError` as soon as
  anything reads the annotation.
- **Keys are exact, and always present.** `'age': int | None` means the key is there and its value may be
  `None`, as in a TypedDict. There's no `NotRequired`, so `user['key']` is always safe and `len()` matches the
  shape.
- **The checker reports an error only where the code would fail at runtime.** `user['nme']` raises `KeyError`,
  so it's an error. `user.get('nme')` returns `None` at runtime, so it isn't an error; its type is exactly
  `None`, and misuse such as `.upper()` is reported where it would actually fail.
- **No shape when the keys can't be known**: `frozendict(some_dict)`, merging with an unshaped side, or
  `frozendict(pairs)` from `(key, value)` pairs (real code has them in a variable, e.g. `zip(keys, values)`).
- **Shapes come only from frozendicts, never from a TypedDict**, even a closed one (PEP 728): a TypedDict is a
  plain `dict` at runtime, so its keys are only the checker's promise (ignored errors, `cast`, `json.loads` with
  extra fields), and an exact shape built from it could be wrong about the actual value.
- **Rejected:** `frozendict[SomeTypedDict]`, a `FrozenDict` base-class package (a frozen dataclass covers
  that), and a copyable `class _(TypedDict)` block in hover (replaced by printing the shape inline).

### Known gaps

- **Notebooks:** VS Code shows no basedpyright diagnostics in `.ipynb` files (an upstream pull-diagnostics issue;
  the server computes them). Use `.py` files.
- **Ruff:** rule UP037's auto-fix unquotes the keys in annotations and breaks the code, so it's disabled in
  [pyproject.toml](pyproject.toml). F821 still flags the keys as undefined names. Ruff special-cases
  `TypedDict[{...}]` but not `frozendict[{...}]`.
- **Literals in tuples:** `frozendict(size=(1, 2))` keeps `tuple[Literal[1], Literal[2]]`, because stock pyright
  solves the value type that way for keyword arguments (`dict(size=(1, 2))` does the same). A dict display
  `frozendict({'size': (1, 2)})` gives `tuple[int, int]`.
- **Other checkers:** mypy, Pylance and stock basedpyright report errors on the `frozendict[{...}]` line itself,
  for example on a `type User = ...` alias.

## Setup

- **The fork:** `../basedpyright-frozendict` (local only), two branches on basedpyright `main`:
  - `frozendict-literal-keys`, the upstream candidate (10 commits): a typeshed stub fix, per-key inference, shape
    notation and annotations, merging, `.get()`/`.copy()`, key hover, `**` unpacking and `match` patterns,
    narrowing and tagged records, completion while building, and `fromkeys`.
  - `frozendict-pypi`, one commit on top: support for the PyPI package. **Keep this one checked out and build
    from it**, so every project gets both.

  Changes to the built-in support go on `frozendict-literal-keys`; then `git rebase frozendict-literal-keys` on
  `frozendict-pypi`. Only PyPI-specific changes go on `frozendict-pypi`. Rebuild with
  `npx pnpm@11.21.0 run build:cli:dev` in the fork, then reload VS Code.
- **VS Code runs the fork** through the wrapper `.venv/bin/basedpyright-langserver` (with
  `basedpyright.importStrategy: fromEnvironment`). Delete the wrapper to go back to the bundled basedpyright.
  The usual window is the `../frozendict-dev.code-workspace` workspace. dream-robot has the same wrapper, with
  its stock script saved next to it as `basedpyright-langserver.stock`. A `uv sync` that reinstalls basedpyright
  overwrites a wrapper.
- **Comparing against stock basedpyright:** open `../playground-stock` in a second window. It has basedpyright
  1.40.2 from PyPI and symlinks to the demo files. (There's one basedpyright server per window, so the two can't
  share a workspace.)
- **Checking from the shell:**
  `node ../basedpyright-frozendict/packages/pyright/index.js -p pyproject.toml demonstrations.py`
