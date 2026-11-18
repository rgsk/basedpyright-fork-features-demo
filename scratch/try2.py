# A dict / frozendict return annotation now bounds the inferred shape instead of
# erasing it. Hover the variables, or type run[ for key completions.
# (Fork server; reload the window after the rebuild.)

from collections.abc import Callable
from typing import Any


# 1. Annotated with K, V: the keys come from the body, each value is the declared V.
def person() -> dict[str, str]:
    return {'name': 'rahul', 'city': 'delhi'}


p = person()
reveal_type(p)  # before: dict[str, str]    now: dict[{'name': str, 'city': str}]
p['name']  # completion offers 'name' and 'city'


# 2. The declared V wins over the inferred value type.
def rates() -> dict[str, float]:
    return {'lr': 1, 'momentum': 0.9}


reveal_type(rates())  # before: dict[str, float]    now: dict[{'lr': float, 'momentum': float}]
reveal_type(rates()['lr'])  # float (not int): the annotation's intent wins


# 3. Bare -> dict: the inferred value types are kept.
def train(lr: float) -> dict:
    return {'weights': [lr, lr * 2], 'log': 'done'}


run = train(0.1)
reveal_type(
    run
)  # before: dict[Unknown, Unknown]    now: dict[{'weights': list[float], 'log': str}]
reveal_type(run['weights'])  # before: Unknown    now: list[float]
run['log'].append(1)  # now an error: str has no append


# 4. V is Any (or object): inferred value types kept, so the annotation costs nothing.
def config() -> dict[str, Any]:
    return {'lr': 0.1, 'epochs': 3, 'layers': [64, 64]}


reveal_type(config()['epochs'])  # before: Any    now: int
reveal_type(
    config()['layers']
)  # before: Any    now: list[Any] (a container value is inferred against Any)


# 5. frozendict: a wrong key is an error, as with an unannotated function.
def pair(first: int, second: str) -> frozendict[str, int | str]:
    return frozendict(first=first, second=second)


reveal_type(pair(1, 'a'))  # now: frozendict[{'first': int | str, 'second': int | str}]
pair(1, 'a')['third']  # now an error: "third" is not a defined key


# 6. Through a decorator that keeps Callable[P, R].
def cache[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    return fn


@cache
def cached() -> dict:
    return {'hits': 3, 'name': 'x'}


reveal_type(cached()['hits'])  # before: Unknown    now: int


# 7. And on methods.
class Trainer:
    def summary(self) -> dict[str, float]:
        return {'loss': 0.5, 'acc': 0.9}


reveal_type(Trainer().summary())  # now: dict[{'loss': float, 'acc': float}]


# Unchanged: these keep the declared type.


def mismatch() -> dict[str, int]:
    return {'a': 'x'}  # error as before: str doesn't fit int


reveal_type(mismatch())  # dict[str, int]


def branches(flag: bool) -> dict:
    if flag:
        return {'a': 1}
    return {'b': 'x'}  # different keys: no single shape


reveal_type(branches(True))  # dict[Unknown, Unknown]


def from_kwargs(**kw: int) -> dict:
    return dict(**kw)  # no known keys


reveal_type(from_kwargs(a=1))  # dict[Unknown, Unknown]
