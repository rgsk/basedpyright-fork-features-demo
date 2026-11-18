"""Built-in frozendict (PEP 814, Python 3.15): an immutable, hashable dict."""

import json
from collections.abc import Mapping, MutableMapping
from functools import lru_cache


def section(title):
    print(f"\n== {title} ==")


section("Create it like a dict, no import needed")
config = frozendict(gamma=0.99, lr=1e-3)
print(config)
print(frozendict({"a": 1}), frozendict([("a", 1)]), frozendict.fromkeys("xy", 0))

section("Reads work like a dict")
print(config["gamma"], config.get("missing", "default"), "lr" in config, len(config))
print(list(config.keys()), list(config.items()))

section("Writes are blocked")
try:
    config["gamma"] = 0.5
except TypeError as e:
    print("TypeError:", e)
try:
    del config["gamma"]
except TypeError as e:
    print("TypeError:", e)
print("has update/pop/clear?", [hasattr(config, m) for m in ("update", "pop", "clear")])

section("It's a copy, not a view (unlike MappingProxyType)")
source = {"gamma": 0.99}
fd = frozendict(source)
source["gamma"] = 0.5
print("source changed to", source["gamma"], "but frozendict still has", fd["gamma"])

section("Hashable: usable as a dict key or set member")
a = frozendict(x=1, y=2)
b = frozendict(y=2, x=1)
print("a == b:", a == b, "| hash equal:", hash(a) == hash(b))  # order doesn't matter
results = {a: "run 1"}
print("lookup with b:", results[b])
print("set dedupes:", {a, b})
print("equal to a plain dict:", a == {"x": 1, "y": 2})

section("Values must be hashable for hash() to work")
try:
    hash(frozendict(layers=[64, 64]))
except TypeError as e:
    print("TypeError:", e)
print("use a tuple instead:", hash(frozendict(layers=(64, 64))) is not None)

section("Works as an lru_cache argument (a plain dict can't)")


@lru_cache
def train(cfg):
    print("  training with", dict(cfg))
    return cfg["lr"] * 1000


train(frozendict(lr=1e-3, gamma=0.99))
train(frozendict(gamma=0.99, lr=1e-3))  # same config, different order: cache hit
print(train.cache_info())
try:
    train({"lr": 1e-3})
except TypeError as e:
    print("plain dict -> TypeError:", e)

section("'|' returns a new frozendict and leaves the original alone")
bigger = config | {"batch_size": 64}
print(bigger, type(bigger).__name__)
print("original unchanged:", config)

section("Type relationships")
print("isinstance dict:", isinstance(config, dict))  # not a dict subclass
print("isinstance Mapping:", isinstance(config, Mapping))
print("isinstance MutableMapping:", isinstance(config, MutableMapping))
print("json:", json.dumps(config))
