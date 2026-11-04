"""TypedDict features that shaped frozendicts now match too (with the basedpyright fork).

Each case: the TypedDict version and the frozendict version (same keys and types) both pass.
"""

from typing import Literal, TypedDict, Unpack, reveal_type


class UserTD(TypedDict):
    name: str
    age: int


td: UserTD = {'name': 'rahul', 'age': 27}
user = frozendict(name='rahul', age=27)  # frozendict[{'name': str, 'age': int}]


# %% 1. Unpacking into parameters with **: each key goes to the parameter of the same name


def greet(name: str, age: int) -> None:
    print(name, age)


def by_kwargs(**kwargs: Unpack[UserTD]) -> None:
    print(kwargs)


# TypedDict: each key is checked against its own parameter
greet(**td)  # ✅ ok
by_kwargs(**td)  # ✅ ok

# frozendict: each key is checked against its own parameter too (it was str | int: 2 false errors)
greet(**user)  # ✅ ok
by_kwargs(**user)  # ✅ ok


# %% 2. Mapping patterns in match: the captured value has the key's type

match td:
    case {'age': td_age}:
        reveal_type(td_age)  # ✅ TypedDict: int

match user:
    case {'age': user_age}:
        reveal_type(user_age)  # ✅ frozendict: int (it was str | int)


# %% 3. Narrowing a union by a literal field (tagged records)


class CircleTD(TypedDict):
    kind: Literal['circle']
    radius: float


class SquareTD(TypedDict):
    kind: Literal['square']
    side: float


type Circle = frozendict[{'kind': Literal['circle'], 'radius': float}]  # noqa: F821
type Square = frozendict[{'kind': Literal['square'], 'side': float}]  # noqa: F821


def area_td(shape: CircleTD | SquareTD) -> float:
    if shape['kind'] == 'circle':
        reveal_type(shape)  # ✅ TypedDict: CircleTD
        return 3.14 * shape['radius'] ** 2
    return shape['side'] ** 2  # ✅ narrowed to SquareTD


def area(shape: Circle | Square) -> float:
    if shape['kind'] == 'circle':
        reveal_type(shape)  # ✅ frozendict: Circle (it was Circle | Square)
        return 3.14 * shape['radius'] ** 2  # ✅ (it was an error)
    return shape['side'] ** 2  # ✅ narrowed to Square


# %% 4. Narrowing a union by key: 'key' in x


def describe_td(shape: CircleTD | SquareTD) -> float:
    if 'radius' in shape:
        reveal_type(shape)  # ✅ TypedDict: CircleTD
        return shape['radius']
    return shape['side']  # ✅ narrowed to SquareTD


def describe(shape: Circle | Square) -> float:
    if 'radius' in shape:
        reveal_type(shape)  # ✅ frozendict: Circle (it was Circle | Square)
        return shape['radius']  # ✅ (it was an error)
    return shape['side']  # ✅ narrowed to Square


# %% 5. Building one where the expected type needs a literal value (tagged records again)

area_td(
    {'kind': 'circle', 'radius': 1.0}
)  # ✅ TypedDict: 'circle' is checked against Literal['circle']
# ✅ frozendict: 'circle' stays Literal['circle'] where expected (it was widened to str)
area(frozendict(kind='circle', radius=1.0))
circle: Circle = frozendict(kind='circle', radius=1.0)  # ✅
print(describe(circle))


# %% 6. Key completion while building one whose type is known (try it: type at the marked spot)

td_build: UserTD = {'name': 'rahul', 'age': 33}  # ✅ TypedDict: typing  {  offers 'name', 'age'
td_call = UserTD(age=28, name='ds')  # ✅ TypedDict: typing  UserTD(  offers name=, age=

type User = frozendict[{'name': str, 'age': int}]  # noqa: F821
fd_build: User = frozendict(
    {'name': '', 'age': 33}
)  # ✅ frozendict: typing  {  offers 'name', 'age'
fd_call: User = frozendict(
    name='rahul', age=22
)  # ✅ frozendict: typing  frozendict(  offers name=, age=


# %% 7. Not supported by design: (key, value) pairs
# Real code passes pairs that are already in a variable (zip(keys, values)), which the checker
# can't know, and widening the literal types here would change what pyright already infers.
reveal_type(frozendict([('name', 'rahul'), ('age', 27)]))
# frozendict[Literal['name', 'age'], Literal['rahul', 27]]

# %% 8. ✅ fromkeys with literal keys: each key gets the value's type (None without one)
reveal_type(
    frozendict.fromkeys(['lr', 'momentum'], 0.0)
)  # frozendict[{'lr': float, 'momentum': float}]

reveal_type(frozendict(**user, **frozendict.fromkeys(['lr', 'momentum'], 0.0)))
reveal_type(frozendict.fromkeys(['b', 'a', 'b', 'c'], 1))
