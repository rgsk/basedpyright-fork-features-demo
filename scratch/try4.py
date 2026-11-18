# SimpleNamespace shapes: what the fork WOULD show (not built yet).
# Comments show the planned reveal_type output; "today:" is the current fork.
from types import SimpleNamespace
from types import SimpleNamespace as namespace
from typing import Protocol, reveal_type

l = [1, 2]
user = dict(name='rahul', age=26)
# 1. Building one remembers attribute names and types
cfg = namespace(host='localhost', port=8080, debug=False)
reveal_type(cfg)  # SimpleNamespace[{host: str, port: int, debug: bool}]   (today: SimpleNamespace)
reveal_type(cfg.port)  # int   (today: Any)

# 2. Adding and deleting attributes updates the shape
cfg.timeout = 3.5
del cfg.debug
reveal_type(cfg)  # SimpleNamespace[{host: str, port: int, timeout: float}]

# 3. Built from a dict shape (3.13+ positional mapping, or **unpacking)
row = {'id': 1, 'name': 'ada'}
user = SimpleNamespace(row)
user2 = SimpleNamespace(**row, admin=True)
reveal_type(user)  # SimpleNamespace[{id: int, name: str}]
reveal_type(user2)  # SimpleNamespace[{id: int, name: str, admin: bool}]

# 4. And back to a dict shape
reveal_type(vars(user))  # dict[{id: int, name: str}]   (today: dict[str, Any])


# 5. Checked against a Protocol, the way dict shapes are checked against TypedDict
class HasName(Protocol):
    id: int
    name: str


def greet(u: HasName) -> str:
    return f'hi {u.name}'


greet(user)  # ok
greet(SimpleNamespace(id=2, name='bob'))  # ok


# 7. Nesting: each inner namespace keeps its own shape (same as dicts inside dicts)
app = SimpleNamespace(
    name='shop',
    db=SimpleNamespace(host='db.local', port=5432),
    flags={'beta': True},  # a dict shape inside a namespace
)
reveal_type(
    app
)  # SimpleNamespace[{name: str, db: SimpleNamespace[{host: str, port: int}], flags: dict[{'beta': bool}]}]
reveal_type(app.db.port)  # int
reveal_type(app.flags['beta'])  # bool

app.db.user = 'admin'  # a write through a path the checker can follow updates the inner shape
reveal_type(app.db)  # SimpleNamespace[{host: str, port: int, user: str}]

rows = [SimpleNamespace(id=1), SimpleNamespace(id=2)]  # namespaces inside a list
reveal_type(rows[0].id)  # int


# 6. Errors that are silent today (inside a function so this file still runs)
def _errors() -> None:
    cfg.prot  # error: "prot" is not an attribute of SimpleNamespace[{host, port, timeout}]
    cfg.debug  # error: "debug" was deleted above
    cfg.port.upper()  # error: "upper" is not an attribute of "int"
    greet(SimpleNamespace(id=3))  # error: missing "name" for protocol HasName
    greet(SimpleNamespace(id='3', name='x'))  # error: "id" is str, HasName wants int


print(greet(user), cfg)
