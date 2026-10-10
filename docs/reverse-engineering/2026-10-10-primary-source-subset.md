# Strict primary-layer source subset

This custom lowerer accepts a complete bounded ASCII expression:ZStack containing exactly three explicit `Color(.sRGB,red:...,green:...,blue:...,opacity:...)` primary layers,followed by constant integer `.frame(width:...,height:...)`. Layer order is blue/red/green or green/red/blue;each primary occurs once. Alpha literals must represent exact eighths0...8;dimensions are1...64. Newline or semicolon separators are required between layer expressions. Text,variables,other stacks,comments,extra modifiers,arbitrary colors,other color spaces,unsupported order/alpha/geometry,trailing tokens and non-ASCII input fail clearly. Input length is capped4096.

The existing opaque Color.frame expression parser remains separate and unchanged. This is a strict custom expression compiler,not the Swift compiler or general SwiftUI execution. Parsed configuration is revalidated before code generation,including exact keys,integer types,order,dimensions and alpha array. Generated C binds those constants to the independently verified primary-layer kernel;the compiler saves O2 LLVM IR and links that saved IR into import-free WASM. Only compiler file metadata in the first two IR lines is explicitly canonicalized;raw IR is retained and every remaining instruction/IR byte is preserved.

Strict primary-layer ZStack.frame source-to-C-to-saved LLVM IR-to-WASM:16 modules,64 full V8 frames/1,048,576 bytes,28 native-prefix comparisons/20,160 target bytes,64 no-write invalid requests,160 baseline/fault cases per interpreter. Repeat/whitespace IR and module bytes equal. Swift parse-only oracle exposed3 missing-separator acceptances; retained inconclusive seal, enforced newline/semicolon separators, fixed oracle agreement and22 diagnostic holdouts. Final complete pipeline supports;getter/PNG/Canvas distinctions retained.

Six measured native alpha triples in both layer orders produce12 source modules;an exact repeat,whitespace variant,one-pixel geometry and full-capacity64×64 holdouts bring the total16. Each module runs two stride variants and two fresh V8 instances. All16,384 bytes match independent Fraction source-over expectations. Native-compatible17×9/stride80 targets preserve the720-byte padded native callback prefix with separately declared tail. These are reused native targets,not new native acquisitions. Output remains premultiplied;the documented native cgImage/PNG differences remain outside this contract.

Four invalid stride calls per source leave the entire previous allocation unchanged (64 requests). Source checkers embed frozen complete expectations,using native prefixes where measured and independent model expectations for other geometry. V8 and WasmKit verify two strides×five baseline/corruption modes per source. Aggregate checks enforce the expected mismatch count individually before returning sums. Channel,alpha,row-boundary and final-allocation-byte corruption are detected. When a target has no padding or fills the capacity,the boundary/final fault refers to an active pixel instead of nonexistent padding/tail. No nonexistent-region coverage is claimed.

An independent Swift frontend parse-only experiment exposed a real grammar gap:the initial parser accepted layer expressions separated only by spaces/tabs or no separator,while Swift rejected all3. That failed acceptance check is retained as a valid sealed inconclusive investigation,not quarantined for integrity. The parser now requires a newline or semicolon. The corrected independent oracle agrees on one valid and3 invalid controls;22 diagnostic holdouts reject. The complete source/IR/runtime pipeline was rerun after the fix. Native parse-only checks do not establish typechecking or runtime rendering.

Evidence seals:

- `20261010T191558Z-portable-primary-source-subset-004a4903`, SHA256 `4dae9bfa36deeffdf591aa78dbed478482dea9b2e0423969dc37ee7b05034d8e`, supports.
- `20261010T191727Z-portable-primary-source-separators-af88f188`, SHA256 `0486897dfecfb1cc92c4c086dc1dd1b3300070f401a4c4007898c8c3205401b7`, inconclusive.
- `20261010T191744Z-portable-primary-source-separators-316163f0`, SHA256 `fe8dfb73bbb39a1f682e96c35e65320eff96c094f3212d22c04e26694a765135`, supports.
- `20261010T191804Z-portable-primary-source-subset-811cf568`, SHA256 `45f7ac0b391eb74b2580209a237e231ee77d55be31c2857129c14137d69b3f88`, supports.

Final pipeline and corrected syntax seals establish this research task;the early permissive parser is not promoted as final syntax conformance. Compiler/linker/WasmKit hashes are unchanged from the externally pinned portable-layer identity. Swift6.3.3 on macOS26.5.1 build25F80 ARM64 supplies the independent parse-only control. No Xcode windows opened.

Next:execute the exact16 source-derived modules/checkers on existing actual Linux. Linux frontend execution,arbitrary Swift/SwiftUI,native getter/PNG/browser/Canvas equivalence and both milestone acceptance contracts remain open.

304 tests pass,including every20 measured alpha triple/order parser configuration,separator rejection,config injection,independent geometry/padding/tail predictions and existing opaque subset tests.
