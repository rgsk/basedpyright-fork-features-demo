# Roadmap

Ideas parked for later. Fork work goes in `~/Documents/codes/projects/basedpyright-frozendict`, branch `dev`.

## Go-to-definition on dict and frozendict keys

**Done (2026-11-06, fork `dev` 1dd276fb5), first version:** jumps to where the key was first added
(literal key, keyword, adding write, `setdefault`, `fromkeys`, `|` merges), across notebook cells too;
a multi-word key is underlined whole on ctrl+hover. Not done yet: the list of every later write (step 2's
"all origins"), `.get('k')` keys, and find-references. The plan below is kept for those.

Ctrl+click on `'sex'` in `prb['sex']` jumps to where the key was added, as stock pyright already does for
TypedDict keys (it jumps to the `name: str` line in the class). It covers both `dict` and `frozendict`
(builtin and the PyPI package): their shapes live in the same `knownEntries`, so one change serves both.
A frozendict can't be written to, so its keys come only from construction (`frozendict({...})`,
`frozendict(sex=...)`, `frozendict.fromkeys([...])`, `|` merges) and each has exactly one origin.

**Where things are (fork, `packages/pyright-internal/src`):**
- `getDeclInfoForStringNode` (`analyzer/typeEvaluator.ts`) answers go-to-definition on a string. The
  definition provider already calls it. For TypedDicts it finds the field from the string's *expected type*;
  a plain dict needs the type of the object being subscripted instead.
- Shapes are `knownEntries: Map<string, Type>` (`analyzer/types.ts`): key and type, no record of where the
  key came from.

**Plan:**
1. **Record origins** in a map beside `knownEntries`: key → the nodes that wrote it. Keep it out of
   `isTypeSame`, so shapes that differ only in origins still merge in loops and after `if`/`else`.
   Sources: the key in a `{'sex': ...}` literal, the `'sex'` in `prb['sex'] = ...`, the `sex=` keyword in
   `dict(...)`, `frozendict(...)` and `.update(...)`, the string in `fromkeys(['sex'])`. A write appends its node; merges (`a | b`, branch
   joins) keep both sides' nodes.
2. **Go-to-definition:** in `getDeclInfoForStringNode`, when the string is a subscript key and the
   subscripted object has `knownEntries` with that key, return declarations pointing at the stored nodes.
   A key written several times lists every origin (where it was added, then later writes), as pyright does
   for a variable assigned more than once. A frozendict key has exactly one.
3. **Notebook cells:** origins travel with the entries across cells, so a key added in cell 2 and read in
   cell 3 should jump across. Add a test in `chainedSourceFiles.test.ts`.

**Later, maybe:** find-references on a key, as best-effort. It isn't free: `documentSymbolCollector.ts`
collects references by walking name nodes and only handles strings for `__all__`, so key reads need a new
branch there.

**Not doing:** rename of a dict key. A plain dict leaves the code the checker can follow (`json.dumps`,
`**kwargs`, unseen calls), so a rename would update the keys it can see and silently break the rest at
runtime. TypedDict keys are safe to rename only because the class declares them.

**Size:** medium. The new field, every place that creates or merges entries (literals, `dict()`, `.update`,
`|`, index writes, the cell carry-over), the lookup, and tests.

## Upstream quirk: plain words in a call's string argument act like the call

Seen 2026-11-06 in a notebook: in `print(f'image tokens changed by: {before:.3f} ...')`, a plain word of
the string (`changed`) is underlined on ctrl+hover, its hover shows `print`'s signature, and go-to-definition
jumps to `print`'s stub. Stock basedpyright does the same, so it isn't from the fork. **Not fixing for now.**
If it's ever looked at: compare stock and the fork side by side, since the fork's go-to-definition on keys
also handles strings (`getDeclInfoForStringNode`) and must not make this worse.

## ModuleDict shapes on attributes (`self.instr`)

Seen 2026-11-09 in a notebook: `self.instr = nn.ModuleDict(dict(colour=nn.Embedding(...), side=nn.Embedding(...)))`
in `__init__` hovers as `ModuleDict[{'colour': Embedding, 'side': Embedding}]`, but `self.instr` in `forward`
is a plain `ModuleDict`: `self.instr['colour']` reads as `Module`, so `.weight` and the call's types are lost
(a typo'd key stays uncaught even after this, as with globals read in a function). That's the
main way a ModuleDict is used (built in `__init__`, read in `forward`), so it's worth doing next.

```python
import torch
from torch import nn

class UNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.instr = nn.ModuleDict(dict(colour=nn.Embedding(4, 256), side=nn.Embedding(2, 256)))
        self.instr  # ModuleDict[{'colour': Embedding, 'side': Embedding}]

    def forward(self, colour: torch.Tensor, side: torch.Tensor):
        self.instr            # today: ModuleDict         wanted: ModuleDict[{'colour': Embedding, 'side': Embedding}]
        self.instr['colour']  # today: Module             wanted: Embedding
        self.instr['color']   # today: Module, no error   wanted: Module, no error (another method may add it)
        return self.instr['colour'](colour) + self.instr['side'](side)

class Patched(nn.Module):
    def __init__(self):
        super().__init__()
        self.heads = nn.ModuleDict(dict(a=nn.Linear(8, 8)))

    def add_head(self):
        self.heads = nn.ModuleDict()  # assigned outside __init__

    def forward(self, x: torch.Tensor):
        return self.heads['a'](x)     # stays plain: Module
```

**Why:** a member variable's declared type is inferred from its assignments, and that drops the shape on purpose
(`removeDictKnownEntries` in the declared-type loop of `typeEvaluator.ts`): another method may change the dict.

**Plan:** treat it like a global read in a function (fork 53dd37fdb, `getDictTypeInFunction`):
- An attribute whose every assignment is in `__init__` keeps the shape it has at the end of `__init__` when
  read in other methods.
- Mark the entries as an outer scope's (`ClassType.cloneForOuterScopeEntries`): reads get per-key types, but a
  missing key isn't an error (another method may add it) and reads as `Module`, as today.
- **ModuleDict only, at first.** For a plain dict, `self.cache = {}` filled in by other methods is common, and
  `dict[{}]` would mislead. ModuleDicts are almost always built once in `__init__` and only read.
- An assignment outside `__init__`, or a write the checker sees there, keeps it plain.

**Tests:** `based_moduledict/sample.py` (hover in `forward`, per-key reads, no error on a missing key, an
assignment in another method makes it plain); README's ModuleDict table ("attributes are plain" row).

**Size:** small to medium.

## argparse.Namespace shapes from `add_argument` calls

Proposed 2026-11-14, after SimpleNamespace shapes. `args.lr`, `args.epochs`, ... are `Any` today, so a typo'd
option name only fails at runtime. The parser's `add_argument` calls say exactly which attributes `parse_args()`
returns:

```python
p = argparse.ArgumentParser()
p.add_argument('--lr', type=float, default=1e-3)
p.add_argument('--seed', type=int)              # no default: may be None
p.add_argument('--use-amp', action='store_true')

args = p.parse_args()
# Namespace[{lr: float, seed: int | None, use_amp: bool}]   (stock: Namespace, every attribute Any)
args.learning_rate   # error: no such attribute (AttributeError at runtime)
args.seed + 1        # error: seed may be None
```

**Rules:**
- Name: the first long option (`-v, --verbose` → `verbose`), dashes → underscores, `dest=` wins; positional
  arguments by their name.
- Type: `type=` (else `str`); `action='store_true'/'store_false'` → `bool`, `'count'` → `int`, `'append'` →
  `list[T] | None`; `nargs='+'/'*'/N` → `list[T]`; `choices=[...]` of literals → `Literal[...]`.
- `| None` unless it has a `default=` (its type), `required=True`, or is positional.
- Follow the parser variable through its `add_argument` calls in the same function, like a dict's writes.
  Falls back to a plain `Namespace` when it can't read them: a name or option that isn't a literal, subcommands
  (`add_subparsers`), argument groups passed elsewhere, `parse_args(namespace=...)`.
- `parse_known_args()` gives the shape to the first element of its tuple.
- Missing attribute is an error, as for SimpleNamespace (same outer-scope exception).

**Reuse:** SimpleNamespace's attribute entries (`simpleNamespaces.ts`: read hook, printer, completions, Protocol
matching). New: collecting entries from the parser's call flow nodes (like `x.update(...)` for dicts).

**Size:** medium (option-to-type mapping, plus following the parser variable).
