# C-ism → Rust idiom map

The translation table for converting decompiler pseudo-C into idiomatic Rust,
plus the crate-substitution seams. Use it during the domain-design pass of a
reconstruction and during each unsafe→safe slice of a literal lift. Companion
glossary for decompiler-specific artifacts (`undefinedN`, `DAT_`, `CONCAT`):
`references/ghidra-artifacts.md`.

## Law: fidelity before idiom

Every rewrite below must preserve observed semantics. Never invent behavior
the decompiled code does not show: if a NULL check orders two operations, the
Option must keep that order; if an error path frees memory and returns -1, the
Err arm must own the same cleanup. Anything you cannot prove from the listing
becomes a marked stub plus a ledger entry, not a plausible guess.

## Core table

| C-ism in decompiler output | Rust idiom | Notes / cautions |
|---|---|---|
| NULL / sentinel-pointer return | `Option<T>` | A non-null sentinel value (e.g. returning `0xFFFFFFFF`) is still an Option; a *status* return is Result instead. Check which callers test. |
| Error-code return (`int`, `HRESULT`, `BOOL`) | `Result<T, DomainError>` with a domain error enum | Name variants from observed call sites, not guesses. `S_OK`/`E_*` pairs map to `Ok`/`Err`. |
| Out-param written before return (`int* outLen`) | Return tuple / struct from the Rust function | Verify the caller reads the out-param only on success; if it reads it on failure too, mirror that with a partial-result type instead. |
| Magic constant (protocol opcode, state number) | `#[repr(uN)] enum` with named variants + `TryFrom` | `TryFrom<uN>` keeps the raw-value parse path; a `#[non_exhaustive]` `Unknown(uN)` variant is the honest form when unseen values are possible. |
| Bit flags (`flag & 0x02`) | `bitflags`-style struct or match on named constants | Keep the numeric values; they are wire/format facts. |
| `ptr + len` buffer params | `&[T]` / `&mut [T]` slices | If a length is computed *inside* (e.g. `len = *(int*)p - 4`), keep that derivation as a comment or named function, do not hide it in slicing sugar. |
| Fixed array member (`char name[16]`) | Array `[T; N]` or, for strings, `String` only if proven NUL-terminated and not written past | Overlapping/reinterpret casts on fixed arrays are a fidelity red flag; keep the raw array. |
| `malloc`/`free` pairs across functions | Ownership: one owner, `Box`/`Vec`/`String` | Match the *ownership graph*, not the call text. A `free` in a different function means the value moves there. |
| Refcounting (manual inc/dec) | `Rc<T>` / `Arc<T>` | If the count field is embedded in a larger struct, keep the struct; the count *is* the semantic. |
| Shared mutable cell with no owner | `RefCell`/`Mutex` behind a clear owner, or restructure into explicit passing | Prefer restructuring; cell types are a last resort with a ledger note. |
| `goto` to a common cleanup label | A closure-free structure: an inner function, `let`-chained early returns, or `std::ops::ControlFlow` | One cleanup label = one `?`-shaped path. Multiple gotos into one label from different depths may need the body split into helper functions. |
| Multi-level `break` out of nested loops | Labeled `break`/`continue`, or extract the loop into a method returning a value | Never reorder exit conditions; each condition keeps its position. |
| `do { ... } while (x)` on an entry-nonzero condition | `loop { ...; if !x { break; } }` | Do-while has a different first-iteration semantic than `while`. |
| Fall-through `switch` cases | `match` with shared arms; fall-through into shared tail code becomes a nested block or helper | Verify whether the fall-through body was decompiler-recovered *or* is genuine control flow. |
| Vtable call (`(**vtable)(self, ...)`) | `dyn Trait` trait object | Recover the vtable layout first (`references/ghidra-artifacts.md`); each function-pointer slot becomes a trait method in declaration order. |
| RTTI class name compare then static cast | `Any` + downcast, or an enum with per-variant impls | If the dispatch is closed (fixed set of compared names), an enum is the honest model. |
| Static/global mutable state (`DAT_` written at runtime) | Struct field passed explicitly; `OnceLock`/`LazyLock` for init-once; `static mut` is a last resort with a ledger note | Measure before reaching for interior mutability; if the global is a cache, model it as an owned cache struct. |
| Function-pointer callbacks stored in structs | A trait object, or a plain `fn`/closure field when the signature is fixed | C callbacks with a `void* userdata` pair become closures capturing the userdata. |
| Single linked-list chaining (`p->next`) | `Option<Box<Node>>` or a flat `Vec` + indices if the list is cyclic/shared | Cycles and multiple parents disqualify Box-chain models; record the actual shape. |
| Manual byte-wise struct serialization (`*(uint32_t*)p = x`) | `bytemuck`-style casts only when layout is proven, else keep the raw read/write in a small named function | Alignment and endianness are wire facts; an unaligned read stays unaligned (`read_unaligned` equivalent). |
| Threading via Win32/pthread calls | `std::thread` / channel types at the same seam | Keep the synchronization *protocol* (what locks what, in what order) exactly; deadlocks are semantics. |
| Assertion / `__security_check_cookie` artifacts | Drop the artifact; keep the bound check it implies, if any | Stack canary code is compiler injection, not program logic. |

## Not-invented rules

- Never rename semantics to taste: a function that returns a raw status *and*
  writes results stays a two-channel result until every caller is proven.
- Never inline a check the binary performs conditionally (checked only in
  release paths may be absent from the listing — say so in the ledger).
- Width changes visible as `CONCAT`/`ZEXT`/`SUBxx` are the decompiler showing
  integer widening/narrowing; model the arithmetic honestly (`as` casts or
  `from`), not the intrinsic.

## Tests and seams

- Write each function's tests only after re-checking its listing; tests
  authored alongside a never-compiled model are the likeliest source of
  false failures.
- Assert the seam the model can actually reach. When an earlier step in
  the orchestration is itself a hard `Err` seam, `?` propagation makes
  later nominal seams unreachable — the test asserts the earliest
  propagated address. A seam expectation that contradicts a sibling
  test's pinned behavior is the stale side.

## Crate-substitution seams

Replace the C/C++/platform layer with a native Rust crate *at the same seam*:
the boundary where the decompiled code makes calls — not at the semantic level
you wish existed. Match observed call arguments and error handling to the
crate's API, and record the substitution in the ledger (call site → crate API).

| Observed seam | Native substitution |
|---|---|
| ONNX Runtime C API calls (session, tensor, run) | `ort` crate |
| Ad-hoc JSON parse/print over char buffers | `serde_json` (keep the exact accepted grammar — a hand-rolled parser often accepts less than the spec) |
| Win32 file/memory/process APIs (`CreateFileW`, `VirtualAlloc`, ...) | `std::fs`, `std::alloc` or arena crates, process crates at the same boundary |
| STL mangled names: `std::basic_string` | `String` / `Vec<u8>` if binary contents observed |
| `std::vector<T>` | `Vec<T>` |
| `std::pair<A,B>` / `std::tuple<...>` | tuples, or a named struct when fields have roles |
| `std::shared_ptr<T>` | `Arc<T>` (or `Rc<T>` when single-threaded is proven) |
| `std::unique_ptr<T>` / `new`/`delete` | `Box<T>` |
| `std::map` / `std::unordered_map` | `BTreeMap` / `HashMap` (order visibility decides which) |
| OpenSSL/BoringSSL symbol set | a Rust TLS/crypto crate covering the exact operations used |
| zlib/lzma/bzip2 decoder entry points | the corresponding Rust codec crate; verify by round-trip against captured data, not by API shape alone |
| Win32 COM interface calls through vtables | the trait-object model plus a Windows crate (`windows`) at the COM boundary |

Substitution is proven by the differential/test gate: the Rust side must
accept and produce byte-identical results for the inputs the binary handled.
A crate whose API cannot express the observed behavior (partial writes,
weird error codes) is the wrong substitution — keep a thin literal layer for
that slice instead and record why.

## Applying the map (checklist)

1. Identify the C-ism from the listing (not from what the function name
   suggests — names may be recovered or wrong).
2. Choose the idiom; write the Rust shape with fidelity notes where the
   mapping is lossy.
3. Compile (`cargo check`) after the slice; run the differential or ledger
   gate before moving on.
4. Mark every semantic guess in the code and the ledger — inferred-behavior
   annotation, never silent.

A mapping not on this table is expected: record the novel C-ism and your
chosen Rust idiom in the worklog so the owner can harvest it.
