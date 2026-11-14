from types import SimpleNamespace as namespace

user = namespace(name='rahul', age=26)
user.sex = 'male'
print(user.name)
print(user.age)
print(user.sex)
d = vars(user)
print(d['name'])
for k in vars(user):
    print(k, '->', getattr(user, k))


def f() -> namespace:
    return namespace(name='rahul')


u = f()
