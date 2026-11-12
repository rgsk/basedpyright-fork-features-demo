"""Plain dicts remember their keys (basedpyright fork; see README.md).

Stock basedpyright, in this project (typeCheckingMode = "standard", so
strictDictionaryInference is off), shows dict[str, Unknown] for these dicts and Unknown
for every read.

The rule:
    A dict literal remembers its keys. Writes in the same function update that memory.
    Wherever the checker can't follow the dict, it is a plain dict[str, ...] as today.

Hover, reveal_type and errors print the known keys as dict[{'key': type, ...}]. That spelling
is display only: in an annotation it's an error, as in every other checker. Code must not need
the fork; to declare a shape, use a class (TypedDict, NamedTuple, dataclass).
No new errors, except where a read is now precise and the code is really wrong.

Each reveal_type(...) shows the checker's result as a note in the editor (and prints the runtime
type when run). Hover any expression to see its type.
"""

from typing import Any, reveal_type

# %% 🆕 A dict literal remembers its keys, and each key has its own type
user = {'name': 'rahul', 'age': 27, 'details': {'sex': 'male'}}
reveal_type(user)  # dict[{'name': str, 'age': int, 'details': dict[{'sex': str}]}]
reveal_type(user['name'])  # str
reveal_type(user['age'])  # int
reveal_type(user['details']['sex'])  # str (nested literals too)

# dict(...) with keyword arguments works the same way
cfg = dict(lr=1e-3, layers=(64, 64))
reveal_type(cfg)  # dict[{'lr': float, 'layers': tuple[int, int]}]

# Completion: type  user['n  and the editor offers 'name' (already works today)

# A bug you'd hit at runtime now shows up in the editor
try:
    user['age'].upper()  # 🆕 error: Cannot access attribute "upper" for class "int"
except AttributeError as e:
    print('AttributeError at runtime too:', e)

# %% 🆕 Writes in the same function update the known keys
# Writes are checked as today: against the dict's value type (Unknown here, as the literal mixes
# types; a literal like {'x': 0} makes dict[str, int], so writing a str to it is an error)
user['name'] = 2  # changes the key's type
reveal_type(user)  # dict[{'name': int, 'age': int, 'details': dict[{'sex': str}]}]
user['joker'] = 'jhi'  # adds a key
reveal_type(user['joker'])  # str
del user['details']  # removes a key
reveal_type(user)  # dict[{'name': int, 'age': int, 'joker': str}]

# Methods with literal keys update them too
user.update(city='delhi')
user |= {'pin': 110001}
reveal_type(user)  # dict[{'name': int, 'age': int, 'joker': str, 'city': str, 'pin': int}]
user.pop('pin')
reveal_type(user.get('city'))  # str
reveal_type(user.copy())  # dict[{'name': int, 'age': int, 'joker': str, 'city': str}]

# Building new dicts merges the keys (the right side wins, as at runtime)
reveal_type({**user, 'age': '27'})  # dict[{'name': int, 'age': str, 'joker': str, 'city': str}]
reveal_type(user | {'age': 28.5})  # dict[{'name': int, 'age': float, 'joker': str, 'city': str}]

# %% 🆕 A dict comprehension over known keys knows its keys (every key has the value's type)
splits = {'train': [1, 2], 'val': [3]}
sizes = {s: len(splits[s]) for s in splits}  # also splits.keys(), k, v in splits.items(), ['a', 'b']
reveal_type(sizes)  # dict[{'train': int, 'val': int}]
runs = {name: {s: w * len(splits[s]) for s in splits} for name, w in [('trained', 1), ('untrained', 0)]}
reveal_type(runs['trained'])  # dict[{'train': int, 'val': int}]
# With an `if` clause, or a key other than the loop variable, it's a plain dict as today
reveal_type({s: 0 for s in splits if s != 'val'})  # dict[str, int]

# %% 🆕 dict(zip(keys, values)) pairs literal keys with a fixed-length tuple by position
def load_person() -> tuple[str, int]:
    return 'rahul', 27


person = dict(zip(('name', 'age'), load_person()))
reveal_type(person)  # dict[{'name': str, 'age': int}]
reveal_type(person['age'])  # int (stock pyright: str | int)
# Keys from a variable, or values of unknown length (zip stops at the shorter one): plain as today
keys = ('name', 'age')
reveal_type(dict(zip(keys, load_person())))  # dict[Literal['name', 'age'], str | int]

# %% 🆕 Branches: a key keeps every type it can have; a key set in one branch only is forgotten
point = {'x': 0, 'y': 0, 'label': 'origin'}
if len(user) > 3:
    point['x'] = 'far'
    point['color'] = 'red'
reveal_type(point)  # dict[{'x': str | int, 'y': int, 'label': str}] ('color' may be missing)

# %% 🆕 Unknown keys: no error, you get today's type
try:
    reveal_type(user['nme'])  # Unknown, no error (it's a plain dict: some code may have added it)
except KeyError as e:
    print('KeyError at runtime:', e)

# A write with a key the checker can't read forgets every key: it could have changed any of them
scores = {'math': 90, 'art': 75}
for subject in ['math', 'art']:
    scores[subject] = 100
reveal_type(scores)  # dict[str, int] (plain, as today)
scores['math'] = 'A'  # error, as today: "Literal['A']" is not assignable to "int"

# %% 🆕 Inferred return types keep the keys: the dict is new, nobody else has changed it


def make():
    d = {'name': 'rahul', 'age': 27}
    d['admin'] = False
    return d


reveal_type(make())  # dict[{'name': str, 'age': int, 'admin': bool}]
reveal_type(make()['age'])  # int

# %% 🆕 A dict return annotation bounds the shape instead of erasing it
# Each key gets the declared value type; with a bare dict, Any or object, the inferred one.


def rates() -> dict[str, float]:
    return {'lr': 1, 'momentum': 0.9}


def run_train(lr: float) -> dict:
    return {'weights': [lr, lr * 2], 'log': 'done'}


def config() -> dict[str, Any]:
    return {'lr': 0.1, 'epochs': 3}


reveal_type(rates())  # dict[{'lr': float, 'momentum': float}] (stock: dict[str, float])
reveal_type(run_train(0.1)['weights'])  # list[float] (stock: Unknown)
reveal_type(config()['epochs'])  # int (stock: Any)


def mixed(flag: bool) -> dict:  # returns with different keys: the declared type, as today
    return {'a': 1} if flag else {'b': 'x'}


reveal_type(mixed(True))  # dict[Unknown, Unknown]

# %% 🆕 A global read in a function has the keys of the code (and notebook cells) above it

counters = {'hits': 0}


def bump() -> None:
    reveal_type(counters)  # dict[{'hits': int}]
    reveal_type(counters.get('misses'))  # int | None: no error, code before the call may add keys


later = {'a': 1}


def read_later() -> None:
    reveal_type(later)  # dict[{'a': int}] (read top to bottom, as a notebook is: the assignment below doesn't count)


later = {'b': 2}

# %% 🆕 Dicts in a list (or tuple, or dict value) keep their keys


def summarize(losses: list[float]):
    best = min(losses)
    return {'best': best, 'best_epoch': losses.index(best), 'improved': losses[-1] < losses[0]}


rows = [summarize(losses) for losses in [[0.9, 0.4], [0.8, 0.5]]]
reveal_type(rows)  # list[dict[{'best': float, 'best_epoch': int, 'improved': bool}]]
reveal_type(rows[0]['best_epoch'])  # int
by_run = {name: summarize(losses) for name, losses in [('a', [0.9]), ('b', [0.8])]}
reveal_type(by_run['a']['improved'])  # bool

# A write through the list makes its dicts plain: the checker can't tell which one changed
results = [{'loss': 0.4, 'tag': 'a'}, {'loss': 0.5, 'tag': 'b'}]
for i in range(len(results)):
    results[i]['loss'] = 'n/a'
reveal_type(results)  # list[dict[str, Unknown]] (plain, as today); also del, .update(), .append(), results[i] = ...

# %% Where the checker can't follow the dict: plain dict[str, ...], as today


class Settings:
    def __init__(self) -> None:
        self.cfg = {'debug': False, 'level': 'info'}

    def enable(self) -> None:
        self.cfg['debug'] = 'yes'  # another method can change any key

    def show(self) -> None:
        reveal_type(self.cfg)  # dict[str, Unknown] (plain: attributes don't remember keys)




# %% ⚠️ Known hole: a call that changes the dict isn't seen (pyright's narrowing has the same one)


def rename(d: dict[str, str | int]) -> None:
    d['name'] = 5


stale = {'name': 'rahul', 'age': 27}
rename(stale)
reveal_type(stale['name'])  # str, but it's 5 at runtime

# The same with a write through a loop variable: the checker doesn't connect r to the list
logs = [{'loss': 0.4, 'tag': 'a'}]
for r in logs:
    r['loss'] = 'n/a'
reveal_type(logs[0]['loss'])  # float, but it's 'n/a' at runtime

# %% ❌ Not done (by design)

# No shape annotations: declare a shape that crosses functions with a class instead, e.g.
#   class User(TypedDict): name: str; age: int
# A remembered dict isn't assignable to a TypedDict: `t: User = user` errors as today
#   (assigning the literal directly works)
# No errors for a typo'd key or for writes on a remembered dict: for TS-style errors use a
#   TypedDict, or, enforced at runtime, maybe a sealeddict package later
