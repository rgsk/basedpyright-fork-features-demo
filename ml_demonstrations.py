"""PyTorch keeps its types (basedpyright fork; see README.md).

Stock basedpyright loses most types in PyTorch code, because torch declares
nn.Module.__call__ as Callable[..., Any], leaves Sequential.forward unannotated, types
ModuleList and ModuleDict items as plain Module, and typeshed types float ** float as Any.
So layer(x), mlp(x), heads[0], d ** -0.5 and everything computed from them are Any: no
completion, no errors.

The fork:
    - calls a module through its forward: Linear(3, 4)(x) is a Tensor, and hover shows
      def layer(input: Tensor) -> Tensor;
    - remembers what a Sequential, ModuleList or ModuleDict is built from, and keeps it through
      .to()/.cuda()/.train(), through self attributes, and through return annotations
      (-> nn.Sequential);
    - types float ** float, int ** float and pow() of them as float (complex for literal
      numbers that make one).

Hover, reveal_type and errors print them as Sequential[Linear, GELU, Linear],
ModuleList[Block] and ModuleDict[{'key': Linear}]. That spelling is display only, not valid
in annotations: annotate with the plain class (nn.Sequential) and the fork keeps what the body
builds.

Each reveal_type(...) shows the checker's result as a note in the editor (and prints the runtime
type when run).
"""

import math
from typing import reveal_type

import torch
from torch import Tensor, nn

x = torch.randn(5, 4)

# %% 🆕 Calling a module goes through its forward
layer = nn.Linear(4, 8)
reveal_type(layer(x))  # Tensor   (stock: Any)
reveal_type(layer(x).shape)  # Size
# Hover on `layer` in `layer(x)`: def layer(input: Tensor) -> Tensor   (stock: -> Any)


class Block(nn.Module):
    def __init__(self, d: int) -> None:
        super().__init__()
        self.proj = nn.Linear(d, d)

    def forward(self, x: Tensor, scale: float = 1.0) -> tuple[Tensor, float]:
        return self.proj(x), scale


block = Block(4)
reveal_type(block(x))  # tuple[Tensor, float]
reveal_type(block(x, scale=2.0)[0])  # Tensor

# %% 🆕 Sequential remembers its modules, and a call runs through each of them
mlp = nn.Sequential(nn.Linear(4, 16), nn.GELU(), nn.Linear(16, 4))
reveal_type(mlp)  # Sequential[Linear, GELU, Linear]   (stock: Sequential)
reveal_type(mlp(x))  # Tensor   (stock: Any)
reveal_type(nn.Sequential(mlp, Block(4))(x))  # tuple[Tensor, float]: nested, and your own modules
reveal_type(mlp.to('cpu').train())  # Sequential[Linear, GELU, Linear]: .to(), .train() keep it
# Hover on `mlp` in `mlp(x)`: def mlp(input: Tensor) -> Tensor (what the first module takes,
# what the chain returns)

# %% 🆕 ModuleList remembers its module type
blocks = nn.ModuleList([Block(4) for _ in range(3)])
reveal_type(blocks)  # ModuleList[Block]   (stock: ModuleList)
reveal_type(blocks[0])  # Block   (stock: Module)
reveal_type(blocks[1:])  # ModuleList[Block]
for b in blocks:
    reveal_type(b)  # Block
for _i, b in enumerate(blocks):  # enumerate, zip, list(...) too
    reveal_type(b)  # Block
reveal_type([b(x)[0] for b in blocks])  # list[Tensor]

# %% 🆕 ModuleDict built from a dict with literal keys remembers each key's module type
core = nn.ModuleDict(dict(tau=nn.Linear(1, 4), pos=nn.Embedding(3, 4), act=nn.ReLU()))
reveal_type(core)  # ModuleDict[{'tau': Linear, 'pos': Embedding, 'act': ReLU}]
reveal_type(core['tau'])  # Linear   (stock: Module)
reveal_type(core['pos'].weight)  # Tensor
reveal_type(core.to('cpu')['act'])  # ReLU: methods that return self keep the keys
core.update(dict(out=nn.Linear(4, 2)))  # update() with known keys adds them, as |= would
reveal_type(core)  # ModuleDict[{'tau': Linear, 'pos': Embedding, 'act': ReLU, 'out': Linear}]


# %% 🆕 Inside a model: built in __init__, typed in forward (no `list[Block]` annotation needed)
class Model(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.blocks = nn.ModuleList([Block(4) for _ in range(2)])
        self.time_in = nn.Sequential(nn.Linear(1, 4), nn.SiLU(), nn.Linear(4, 4))

    def forward(self, x: Tensor, tau: Tensor) -> Tensor:
        reveal_type(self.blocks)  # ModuleList[Block]
        reveal_type(self.time_in)  # Sequential[Linear, SiLU, Linear]
        x = x + self.time_in(tau[:, None])
        for block in self.blocks:
            x, _ = block(x)
        reveal_type(x)  # Tensor
        return x


reveal_type(Model()(x, torch.rand(5)))  # Tensor


# %% 🆕 A `-> nn.Sequential`, `-> nn.ModuleList` or `-> nn.ModuleDict` annotation keeps what
# the body builds
def make_backbone() -> nn.Sequential:
    return nn.Sequential(nn.Conv2d(3, 32, 5, 2, 2), nn.ReLU(), nn.Conv2d(32, 64, 1))


def make_blocks(n: int) -> nn.ModuleList:
    return nn.ModuleList([Block(4) for _ in range(n)])


def make_heads() -> nn.ModuleDict:
    heads = nn.ModuleDict(dict(tau=nn.Linear(1, 4), act=nn.ReLU()))
    return heads


reveal_type(make_backbone())  # Sequential[Conv2d, ReLU, Conv2d]   (stock: Sequential)
grid = make_backbone()(torch.rand(2, 3, 32, 32))
reveal_type(grid)  # Tensor   (stock: Any)
reveal_type(make_blocks(2))  # ModuleList[Block]
reveal_type(make_heads())  # ModuleDict[{'tau': Linear, 'act': ReLU}]   (stock: ModuleDict)
reveal_type(make_heads()['act'])  # ReLU   (stock: Module)


# Bodies that build different ones, or ones the checker can't see, keep the annotation.
def either(flag: bool) -> nn.Sequential:
    return nn.Sequential(nn.Linear(4, 4)) if flag else nn.Sequential(nn.ReLU())


reveal_type(either(True))  # Sequential

# %% 🆕 float ** float is float, not Any
head_size = 16
q = torch.randn(2, 3, 16)
k = torch.randn(2, 3, 16)
reveal_type(head_size**-0.5)  # float   (stock: Any)
reveal_type(32**0.5)  # float
reveal_type(pow(2.0, 0.5))  # float
scores = q @ k.transpose(-1, -2) * head_size**-0.5
reveal_type(scores)  # Tensor   (stock: Any: Tensor * Any is Any)
reveal_type(scores.softmax(-1))  # Tensor
reveal_type(math.sqrt(32))  # float: the usual workaround, no longer needed

# Literal numbers that make a complex number give complex, as at runtime.
reveal_type((-8) ** 0.5)  # complex   ((-8) ** 0.5 == 1.7e-16+2.8j)
reveal_type(-(8**0.5))  # float: -8 ** 0.5 is -(8 ** 0.5)
reveal_type((-8) ** 2.0)  # float   (stock: complex, whatever the exponent)
# Unchanged: int ** int stays Any (an int or a float, depending on the exponent's sign), and
# a non-literal negative base with a fractional exponent is still typed float.


# %% 🆕 Errors that stock basedpyright misses (inside a function so this file runs)
def _errors() -> None:
    layer()  # error: Argument missing for parameter "input"
    block(x, scal=2.0)  # error: No parameter named "scal"
    heads = nn.ModuleDict({'a': nn.Linear(4, 4)})
    heads['b']  # error: Could not access item in ModuleDict ("b" is not a defined key)
    mlp(x).shpe  # error: Cannot access attribute "shpe" for class "Tensor"
    s: str = head_size**-0.5  # error: "float" is not assignable to "str"
    # Not caught, as in stock: nn.Module defines __getattr__, so any attribute name passes
    # (blocks[0].prj is a Block, but .prj isn't an error).


print(mlp(x).shape, grid.shape, scores.shape)
