# Why "a Sequential call is always a Tensor" would be wrong: the last module can return something else.
from typing import NamedTuple

import torch
from torch import Tensor, nn


class Out(NamedTuple):
    logits: Tensor
    value: Tensor


class DictHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin = nn.Linear(16, 4)

    def forward(self, x: Tensor) -> dict[str, Tensor]:
        return {'logits': self.lin(x), 'value': x.mean(-1)}


class TupleHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin = nn.Linear(16, 4)

    def forward(self, x: Tensor) -> Out:
        return Out(self.lin(x), x.mean(-1))


x = torch.zeros(2, 4)
a = nn.Sequential(nn.Linear(4, 16), nn.GELU(), DictHead())
b = nn.Sequential(nn.Linear(4, 16), nn.GELU(), TupleHead())

reveal_type(a(x))  # dict[{'logits': Tensor, 'value': Tensor}]   (always Tensor: Tensor)
reveal_type(b(x))  # Out                                          (always Tensor: Tensor)
print(a(x)['logits'].shape)  # runs: torch.Size([2, 4])
print(b(x).logits.shape)  # runs: torch.Size([2, 4])

# What "always Tensor" would make of them: both lines run fine above, but are errors on a Tensor
t = torch.zeros(2, 16)
t['logits']  # error: "Literal['logits']" cannot be assigned to parameter "indices" of "__getitem__"
t.logits  # error: Cannot access attribute "logits" for class "Tensor"
