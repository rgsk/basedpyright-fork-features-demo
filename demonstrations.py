"""frozendict literal-key inference (basedpyright fork).

Each reveal_type(...) shows the checker's result as a note in the editor (and prints the runtime
type when run). Hover any expression to see its type. Kept as a .py file because VS Code shows
no basedpyright diagnostics in notebooks.
"""

from typing import Literal, TypedDict, Unpack, reveal_type

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

# %% ✅ .get() and .copy(): every key in the shape is always present
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

# %% ✅ Like a TypedDict: ** unpacking, match patterns, narrowing, completion
# Each feature is shown next to the TypedDict version it matches.


class UserTD(TypedDict):
    name: str
    age: int


td: UserTD = {'name': 'rahul', 'age': 27}


# ** unpacking into parameters: each key goes to the parameter of the same name
def greet(name: str, age: int) -> None:
    print(name, age)


def by_kwargs(**kwargs: Unpack[UserTD]) -> None:
    print(kwargs)


greet(**td)  # TypedDict
greet(**user)  # frozendict: ok too (it was 2 errors, every key read as str | int)
by_kwargs(**user)  # ok, against Unpack[UserTD]

# Mapping patterns: the captured value has the key's type
match user:
    case {'age': user_age}:
        reveal_type(user_age)  # int (TypedDict: int)


# Unions of shapes narrow by a literal field or by key (tagged records)
type Circle = frozendict[{'kind': Literal['circle'], 'radius': float}]  # noqa: F821
type Square = frozendict[{'kind': Literal['square'], 'side': float}]  # noqa: F821


def area(shape: Circle | Square) -> float:
    if shape['kind'] == 'circle':
        reveal_type(shape)  # frozendict[{'kind': Literal['circle'], 'radius': float}]
        return 3.14 * shape['radius'] ** 2
    return shape['side'] ** 2  # narrowed to Square


def describe(shape: Circle | Square) -> float:
    if 'radius' in shape:  # a shape's keys are exact, so this narrows too
        return shape['radius']
    return shape['side']


# A literal value stays literal where the expected type needs it ('circle' isn't widened to str)
circle: Circle = frozendict(kind='circle', radius=1.0)
print(area(circle), describe(frozendict(kind='square', side=2.0)))

# Key completion while building one whose type is declared (try it in the editor):
#   typing  {  in  u: User = frozendict({   offers 'name', 'age'
#   typing  (  in  u: User = frozendict(    offers name=, age=

# %% ✅ fromkeys with literal keys: each key gets the value's type (None without one)
reveal_type(
    frozendict.fromkeys(['lr', 'momentum'], 0.0)
)  # frozendict[{'lr': float, 'momentum': float}]
# several keys sharing a default, merged into a known shape
reveal_type(frozendict(**user, **frozendict.fromkeys(['lr', 'momentum'], 0.0)))
#   frozendict[{'name': str, 'age': int, 'lr': float, 'momentum': float}]

# %% No shape by design: built from a dict (its keys aren't known to the checker)
d = {'a': 1}
reveal_type(frozendict(d)['a'])  # int via _VT, but a typo key would not be flagged

# From (key, value) pairs: no shape. Real code has the pairs in a variable (zip(keys, values)).
reveal_type(frozendict([('name', 'rahul'), ('age', 27)]))
#   frozendict[Literal['name', 'age'], Literal['rahul', 27]]
