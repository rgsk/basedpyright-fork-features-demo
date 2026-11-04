"""frozendict literal-key inference (basedpyright fork).

Each reveal_type(...) shows the checker's result as a note in the editor (and prints the runtime
type when run). Hover any expression to see its type. Kept as a .py file because VS Code shows
no basedpyright diagnostics in notebooks.
"""

from typing import reveal_type

# %% ✅ Works today
user = frozendict(name='rahul', age=27)

# Each key keeps its own type (stock basedpyright says str | int for both)
reveal_type(user['name'])  # str
reveal_type(user['age'])  # int

# A typo'd key is an error: "Could not access item in frozendict"
try:
    user['nme']
except KeyError as e:
    print('KeyError at runtime too:', e)

# Key completion: type  user[  and the editor offers "name", "age"

# A dict display works too
cfg = frozendict({'lr': 1e-3, 'layers': (64, 64)})
reveal_type(cfg['lr'])  # float
reveal_type(cfg['layers'])  # tuple[int, int]


# The shape survives an inferred return type
def make():
    return (frozendict(name='a', age=1), 1)


reveal_type(make())  # tuple[frozendict[{'name': str, 'age': int}], Literal[1]]
reveal_type(make()[0]['age'])  # int

# Hover, reveal_type and error messages all show the shape
reveal_type(user)  # frozendict[{'name': str, 'age': int}]

# The shape can be written in annotations: frozendict[{'key': type, ...}] (keys are exact)
type User = frozendict[{'name': str, 'age': int}]  # noqa: F821 (ruff reads the keys as names)


def load() -> User:  # a declared return type that keeps the shape
    return frozendict(name='rahul', age=27)


reveal_type(load()['age'])  # int
missing: User = frozendict(name='rahul')  # error: "age" is required in "User"
extra: User = frozendict(name='rahul', age=27, city='delhi')  # error: "city" is undefined

# %% ✅ Merging keeps the shape (the right side wins, as at runtime)
defaults = frozendict(lr=1e-3, epochs=10)
reveal_type(defaults | {'epochs': 20})  # frozendict[{'lr': float, 'epochs': int}]
reveal_type(defaults | frozendict(epochs='all'))  # frozendict[{'lr': float, 'epochs': str}]
reveal_type(frozendict(defaults, batch=32))  # ... 'batch': int}]
reveal_type(frozendict({**defaults, 'epochs': 20}))  # frozendict[{'lr': float, 'epochs': int}]
reveal_type(frozendict(**defaults, batch=32))  # ... 'batch': int}]
cfg2 = defaults
cfg2 |= {'epochs': 20}
reveal_type(cfg2['epochs'])  # int
reveal_type({'epochs': 20} | defaults)  # dict[str, int | float]: a dict on the left makes a dict

# %% .get() and .copy(): every key in the shape is always present
reveal_type(user.get('age'))  # int (the default is never used)
reveal_type(user.get('age', 0))  # int
reveal_type(user.copy())  # frozendict[{'name': str, 'age': int}] (copy() returns self)
# An unknown key isn't an error (it doesn't fail at runtime): you get exactly the default
nme = user.get('nme')
reveal_type(nme)  # None
reveal_type(user.get('nme', 'x'))  # str
try:
    nme.upper()  # error: "upper" on None, where runtime fails too
except AttributeError as e:
    print('AttributeError:', e)


# %% Declared return types: declare the shape to keep it


def make_user() -> frozendict[{'name': str, 'age': int}]:
    return frozendict(name='a', age=1)


reveal_type(make_user()['age'])  # int


def make_user_plain() -> frozendict[str, str | int]:  # no shape declared: keys are unknown
    return frozendict(name='a', age=1)


reveal_type(make_user_plain()['age'])  # str | int

# %% No shape by design: built from a dict (its keys aren't known to the checker)
d = {'a': 1}
reveal_type(frozendict(d)['a'])  # int via _VT, but a typo key would not be flagged
