# Native observer dictionary removal boundaries

The previously recovered invalidation-token closure targets now lead into actual specialized dictionary implementation bodies. A finite checker verifies their selected instruction/dataflow sites and independently decodes twelve ARM64 BL targets. This advances static R2 observer deregistration; it does not establish live Canvas cancellation or final resource cleanup.

Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64. Foundation image SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`. The earlier invalidation seals were verified against published anchors before extension. The retained Xcode bridge remains responsive; no new window, attachment or live transport capture was attempted.

## Instruction-derived paths

The isolated forwarder loads its key from context offset `0x10`, supplies a stack value whose first sixteen bytes are the mapped pair `(0,1)`, zeroes the following sixteen bytes and calls setter `0xedf78` from `0x42634`. The full sixteen-byte constant at `0x133190` is independently checked through the Mach-O file mapping; the isolated remover also reads the same mapped constant. No named Swift Optional ABI case is assigned merely from these words.

The setter compares the copied local pair against `(0,1)`: equality at `0xedfbc` branches to `0xee018` and calls isolated remover `0xee834` at `0xee040`. The alternative path calls `updateValue` target `0xee23c`. Value-witness copying and typed native execution remain unverified; this is a static sentinel branch, not a runtime nil injection.

The concurrent forwarder calls remover `0xee75c` from `0x428e8`. After lookup, a clear found bit at `0xee784` skips mutation and returns zero words. The found path checks uniqueness, branches to copy target `0x13130` when required, extracts the old value, calls native bucket deletion `0x18158`, and stores dictionary storage back. It then scans the ordered identifier array and calls remove-at `0xf82dc`. Failure to find an ordered key after successful dictionary lookup reaches `brk #1` at `0xee7e8`.

Isolated remover `0xee834` checks its returned pair against `(0,1)`. That sentinel path bypasses ordered-key removal and writes the mapped sentinel to its result. The other path scans for the key, traps at `0xee8a0` if absent, and calls the same array remove-at target from `0xee8d4`.

## Concrete storage boundaries

Native bucket deletion builds a mask clearing the selected occupancy bit and stores it at `0x182a8`. It decrements the 64-bit count at storage offset `0x10`, with an overflow branch to a trap, then increments/stores the 32-bit word at offset `0x24`. The word is not named as a Canvas generation field. The checker constrains mask construction, count/counter offsets and arithmetic; it is not a full interpreter of hash relocation or all collision cases.

Identifier-array remove-at checks uniqueness, with copy target `0x3c6bc` on its alternate path. It checks the index against count, loads/stores the removed eight-byte identifier, computes the trailing-byte length, calls `memmove` stub `0x13106c`, decrements/stores count and writes the array storage back. Bounds failure traps at `0xf8360`. Copy helpers and runtime allocation/release effects remain separate from these selected storage/call boundaries.

## Verification and remaining scope

The seven-entry checker rejects missing/duplicate bodies and repeated addresses. Synthetic tests independently encode call immediates with deliberately unrelated textual call annotations, then corrupt target bytes, sentinel/lookup/uniqueness/ordered-key/bounds branches, storage offsets, bitmap operations, count arithmetic and array shift lengths. Every one of the sixteen constant bytes is corrupted separately, and truncated mapping rejects. Strict Boolean configuration is enforced. All 150 tests pass.

Five new sealed runs retain discovery, dependency bodies and successive checker strengthening, including the final twelve-target check. Anchors and scoped observations are published in [sanitized evidence](../../research/evidence/observer-dictionary-removal-2026-10-09.json). Same-address native dictionary aliases remain grouped; symbol names alone do not assign unique concrete type semantics. Raw native bodies remain local.

R2 stays open for actual selected-flow callback association, value-witness effects, native dictionary contents/races, abandoned replies and transport/resource cleanup. No private Swift ABI binding, process attachment, system protection change, user process termination or Xcode window opening occurred.
