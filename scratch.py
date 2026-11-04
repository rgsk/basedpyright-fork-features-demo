user = frozendict(name='rahul', age=27)
# name = user['name']
# age = user['age']

# print(name, age)
# print(user['age'])
# cfg = frozendict({'lr': 1e-3, 'layers plus': (64, 64)})
# print(cfg['layers plus'])


def make():
    return frozendict(name='a', age=1, sex='male')


u = make()
print(u['name'])
print(u['sex'])
sex = u['sex']
print(sex)
age = user.get('age', 0)
print(age)
merged = user | {'city': 'delhi'}
city = merged['city']
print(city)


from typing import NotRequired, TypedDict, reveal_type


class User(TypedDict):
    name: str
    age: int


def fn() -> User:
    return User(name='rahul', age=33)


def f() -> frozendict[{'name': str, 'age': int}]:
    # return frozendict(name='rahul', age=None)
    return frozendict({'name': 'rahul', 'age': 1})


user = f()

print(user['name'])
age = user['age']
print(age)
a = user.get('age', 27)
print(a)
# k: frozendict = frozendict(name='rahul')
# print(k)
# d = {'size': (1, 2)}
# d1 = dict(size=(1, 2))


# d = frozendict({'size': (1, 2)})
# print(d['size'])
# print(d.get('dsdsdsds'))
# print(d.get('size'))


# %% `int | None` means "the key is always there, its value may be None", for TypedDict too.
# A key that may be MISSING is a different thing: TypedDict spells it NotRequired[...].


class PersonTD(TypedDict):
    name: str
    age: int | None  # present, maybe None


p1: PersonTD = {'name': 'rahul', 'age': None}  # ok
p2: PersonTD = {'name': 'rahul'}  # error: "age" is required in "PersonTD"
reveal_type(p1['age'])  # int | None: always safe to read
name = p1.get('names')
print(name)


class MaybeAgeTD(TypedDict):
    name: str
    age: NotRequired[int]  # may be missing


m: MaybeAgeTD = {'name': 'rahul'}  # ok
try:
    m['age']  # error: "age" is not a required key: reading it may raise KeyError
except KeyError as e:
    print('KeyError at runtime:', e)
reveal_type(m.get('age', 8))  # int | None: the only safe read


# frozendict shapes behave like PersonTD: every listed key is always there.
type Person = frozendict[
    {
        'name': str,
        'age': int | None,
    }
]

f1: Person = frozendict(name='rahul', age=None)  # ok
f2: Person = frozendict(name='rahul')  # error: "age" is required in "Person"
reveal_type(f1['age'])  # None (narrowed to the value just assigned)


def read(person: Person) -> None:
    reveal_type(person['age'])  # int | None: always safe to read


# No NotRequired for frozendict on purpose: f1['age'] stays safe, len() and iteration match the
# shape, and writing age=None in the one place a frozendict is built is cheap.
