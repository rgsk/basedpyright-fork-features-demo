"""TypedDict: the declared-shape cousin of what the frozendict fork infers."""

from typing import NotRequired, ReadOnly, TypedDict, reveal_type


class User(TypedDict):
    name: str
    age: int


user: User = {'name': 'rahul', 'age': 27}

# Each key keeps its own type
reveal_type(user['name'])  # str
reveal_type(user['age'])  # int

# A typo'd key is an error
try:
    user['nme']
except KeyError as e:
    print('KeyError:', e)

# Key completion: type  user[  and the editor offers "name", "age"

# Hover shows the shape by name
reveal_type(user)  # User

# .get() knows each key's type
reveal_type(user.get('age'))  # int  (required key)
reveal_type(user.get('age', 0))  # int
reveal_type(user.get('nme'))  # Any | None  (unknown key, no error)

# Missing or extra keys are errors at construction
bad: User = {'name': 'rahul'}  # error: "age" is required
extra: User = {'name': 'rahul', 'age': 27, 'city': 'delhi'}  # error: "city" is undefined


# Optional keys: NotRequired
class Profile(TypedDict):
    name: str
    bio: NotRequired[str]


p: Profile = {'name': 'rahul'}
reveal_type(p.get('bio'))  # str | None


# Immutable keys: ReadOnly (the closest TypedDict gets to frozendict)
class Config(TypedDict):
    lr: ReadOnly[float]


cfg: Config = {'lr': 1e-3}
cfg['lr'] = 0.5  # error: "lr" is read-only

# Differences from the frozendict fork:
# - the shape must be declared up front (class User);
#   the fork infers it from frozendict(name=..., age=...)
# - at runtime a TypedDict is a plain, mutable dict; frozendict is immutable and hashable
print(type(user).__name__)  # dict
