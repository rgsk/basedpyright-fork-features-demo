"""SimpleNamespace remembers its attributes (basedpyright fork; see README.md).

Stock basedpyright types every attribute of a types.SimpleNamespace as Any (its stub
declares __getattribute__ -> Any), so typos and wrong types go unnoticed, and passing one
where a Protocol is expected is an error.

The rule (the same as a dict's keys):
    SimpleNamespace(...) remembers its attributes. Writes in the same function update that
    memory (ns.x = ..., del ns.x, setattr/delattr with a literal name). Wherever the checker
    can't follow the namespace, it is a plain SimpleNamespace, as today.

Unlike a dict's missing key, reading an attribute the namespace doesn't have is an error:
at runtime it raises AttributeError.

Hover, reveal_type and errors print the attributes as SimpleNamespace[{name: type, ...}].
That spelling is display only, not valid in annotations (SimpleNamespace isn't subscriptable
at runtime). To declare a shape, use a Protocol: a namespace with matching attributes fits it.

Each reveal_type(...) shows the checker's result as a note in the editor (and prints the runtime
type when run).
"""

from types import SimpleNamespace
from types import SimpleNamespace as namespace
from typing import Protocol, reveal_type

# %% 🆕 SimpleNamespace(...) remembers its attributes, each with its own type
cfg = SimpleNamespace(host='localhost', port=8080, debug=False)
reveal_type(cfg)  # SimpleNamespace[{host: str, port: int, debug: bool}]
reveal_type(cfg.port)  # int   (stock: Any)

short = namespace(a=1)  # an import alias works the same way
reveal_type(short)  # SimpleNamespace[{a: int}]

# %% 🆕 Writes update the attributes
cfg.timeout = 3.5
del cfg.debug
setattr(cfg, 'retries', 3)
reveal_type(cfg)  # SimpleNamespace[{host: str, port: int, timeout: float, retries: int}]

ns = SimpleNamespace()  # filled attribute by attribute
ns.a = 1
ns.b = 'x'
reveal_type(ns)  # SimpleNamespace[{a: int, b: str}]

# %% 🆕 Built from a dict with known keys, and back
row = {'id': 1, 'name': 'ada'}
user = SimpleNamespace(row)  # Python 3.13+
user2 = SimpleNamespace(**row, admin=True)
reveal_type(user)  # SimpleNamespace[{id: int, name: str}]
reveal_type(user2)  # SimpleNamespace[{id: int, name: str, admin: bool}]
reveal_type(vars(user))  # dict[{'id': int, 'name': str}]

# %% 🆕 Nesting: inner namespaces and dicts keep their shapes
app = SimpleNamespace(
    name='shop',
    db=SimpleNamespace(host='db.local', port=5432),
    flags={'beta': True},
)
reveal_type(app.db.port)  # int
reveal_type(app.flags['beta'])  # bool
app.db.user = 'admin'
reveal_type(app.db)  # SimpleNamespace[{host: str, port: int, user: str}]
app.db.port = '5433'  # writes and deletes through a path change the outer shape too
del app.db.host
reveal_type(app)  # SimpleNamespace[{name: str, db: SimpleNamespace[{port: str, user: str}], flags: dict[{'beta': bool}]}]

rows = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
reveal_type(rows[0].id)  # int


# %% 🆕 A Protocol is the declared shape: matching namespaces fit it
class HasName(Protocol):
    id: int
    name: str


def greet(u: HasName) -> str:
    return f'hi {u.name}'


print(greet(user))  # ok (stock: error, "id" is not present)
print(greet(SimpleNamespace(id=2, name='bob', extra=None)))  # ok: extra attributes are fine

# Completion inside SimpleNamespace( where a Protocol is expected offers the
# attributes still missing (here name=, typed str; id is already given)
carol: HasName = SimpleNamespace(id=3, name='carol')


# %% 🆕 Errors that stock basedpyright misses (inside a function so this file runs)
def _errors() -> None:
    local = SimpleNamespace(host='h', port=1, debug=False)
    del local.debug
    local.prot  # error: Cannot access attribute "prot"
    local.debug  # error: deleted above
    local.port.upper()  # error: "upper" is not an attribute of "int"
    cfg.prot  # no error: a global read in a function may have gained attributes before the call
    greet(SimpleNamespace(id=3))  # error: "name" is not present
    greet(SimpleNamespace(id='3', name='x'))  # error: "id" is str


print(cfg, app)
