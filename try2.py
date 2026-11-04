"""How to give a function that returns a frozendict a declared return type that keeps the shape.

Hover idea: hovering a shaped frozendict shows a copyable TypedDict, e.g.

    class _(TypedDict):
        name: str
        age: int

Below: what you can do with that class today, and what `frozendict[User]` would add.
"""

from typing import ReadOnly, TypedDict, reveal_type


class User(TypedDict):
    name: str
    age: int


# %% The problem: only an INFERRED return type keeps the shape


def inferred():
    return frozendict(name='rahul', age=27)


def declared() -> frozendict[str, str | int]:
    return frozendict(name='rahul', age=27)


reveal_type(inferred()['age'])  # int        (fork keeps the shape)
reveal_type(declared()['age'])  # str | int  (the annotation can't spell the shape)


# %% Option A: paste the hover into a TypedDict, use it as the return type -> error


def option_a() -> User:
    return frozendict(name='rahul', age=27)  # error: frozendict is not assignable to "User"


class RoUser(TypedDict):  # all keys ReadOnly: still an error
    name: ReadOnly[str]
    age: ReadOnly[int]


def option_a_readonly() -> RoUser:
    return frozendict(name='rahul', age=27)  # error: same


# A TypedDict always means a real dict at runtime; frozendict is not a dict subclass.


# %% Option A2: keep the TypedDict, return a plain dict instead (works today, stock checkers too)


def option_a2() -> User:
    return {'name': 'rahul', 'age': 27}


reveal_type(option_a2()['age'])  # int
option_a2()['age'] = 99  # allowed: it's a mutable dict again
try:
    cache = {option_a2(): 'run 1'}  # error: dict is unhashable (frozendict was the point)
except TypeError as e:
    print('runtime too:', e)


# %% Option B: frozendict[User], new fork-only meaning: "a frozendict with User's keys"


def option_b() -> frozendict[User]:  # today: error, "expected 2 type arguments"
    return frozendict(name='rahul', age=27)  # today: error, key type read as User


reveal_type(option_b()['age'])  # today: Unknown + error ('age' is not a User)   want: int
try:
    option_b()['nme']  # today: error ('nme' is not a User)   want: "nme" is not a defined key
except KeyError as e:
    print('KeyError:', e)
cache_b = {option_b(): 'run 1'}  # hashable, immutable: fine

# Runtime: Python accepts it (frozendict[User] is just a GenericAlias), so this file runs.
# Other checkers (mypy, Pylance, stock basedpyright) keep today's errors on option_b.
print(option_b.__annotations__)
