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
