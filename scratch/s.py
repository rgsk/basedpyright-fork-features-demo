# What got fixed today (fork dev, uncommitted). Hover the names; "before:" is the old fork.
from dataclasses import dataclass
from types import SimpleNamespace as namespace
from typing import reveal_type

# 1. Values keep their own types (SimpleNamespace's **kwargs were Any)
app = namespace(
    name='shop',
    version=(1, 4),
    tags=['web', 'api'],
    db=namespace(host='localhost', port=5432, user='admin'),
)
reveal_type(app.version)  # tuple[int, int]   (before: Any)
reveal_type(app.tags)  # list[str]   (before: list[Any])


# 2. A function reading a global: nested namespaces get the same leniency
def check() -> str:
    app.sssss  # no error (unchanged): code before the call may have added it
    db = app.db
    return db.users  # no error now   (before: error, inconsistent with app.sssss)


# 3. A -> SimpleNamespace annotation keeps the shape, as -> dict does
def make() -> namespace:
    return namespace(name='rahul', age=26)


reveal_type(make())  # SimpleNamespace[{name: str, age: int}]   (before: SimpleNamespace)

# 4. Hover on an attribute: "(variable) port: int"   (before: "(function) port: int")
app.db.port


@dataclass
class User:
    name: str
    age: int


u = User('rahul', 26)
print(u.name)
print(u.age)
