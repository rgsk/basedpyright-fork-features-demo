# dict(zip(keys, values)): which cases get a shape
from typing import reveal_type



class Image: ...  # stands in for NDArray[np.uint8] (numpy isn't installed here)


def load_person() -> tuple[str, int]:
    return 'rahul', 27


def load_cameras(name: str) -> tuple[Image, Image]: ...


def load_names() -> list[str]:
    return ['a', 'b']


def load_rest() -> tuple[str, *tuple[int, ...]]:
    return 'a', 1, 2


# %% ✅ Supported: literal keys written in the call + a fixed-length tuple of the same length

# Values from a function returning a tuple
person = dict(zip(('name', 'age'), load_person()))
reveal_type(person)  # dict[{'name': str, 'age': int}]
reveal_type(person['age'])  # int

# Keys as a list display instead of a tuple
reveal_type(dict(zip(['name', 'age'], load_person())))  # dict[{'name': str, 'age': int}]

# Values as a tuple display (literals widened: 'rahul' -> str, 27 -> int)
reveal_type(dict(zip(('name', 'age'), ('rahul', 27))))  # dict[{'name': str, 'age': int}]

# Values from a variable typed as a tuple
p = load_person()
reveal_type(dict(zip(('name', 'age'), p)))  # dict[{'name': str, 'age': int}]

# strict=True is allowed
reveal_type(dict(zip(('name', 'age'), load_person(), strict=True)))  # dict[{'name': str, 'age': int}]

# frozendict: exact keys, so a typo is an error
cams = frozendict(zip(('top', 'wrist'), load_cameras('robot')))
reveal_type(cams)  # frozendict[{'top': Image, 'wrist': Image}]
cams['wirst']  # error: 'wirst' is not a key

# %% ❌ Not supported: plain type, as stock pyright gives it

# Keys from a variable
keys = ('name', 'age')
reveal_type(dict(zip(keys, load_person())))  # dict[Literal['name', 'age'], str | int]

# Values of unknown length (zip may stop early, so a key could be missing)
reveal_type(dict(zip(('a', 'b'), load_names())))  # dict[Literal['a', 'b'], str]

# Lengths differ
reveal_type(dict(zip(('name',), load_person())))  # dict[Literal['name'], str | int]
reveal_type(dict(zip(('a', 'b', 'c'), load_person())))  # dict[Literal['a', 'b', 'c'], str | int]

# Tuple with an unbounded part
reveal_type(dict(zip(('a', 'b'), load_rest())))  # dict[Literal['a', 'b'], str | int]

# Keys that aren't literals
name = input()
reveal_type(dict(zip((name, 'age'), load_person())))  # dict[str, str | int]
