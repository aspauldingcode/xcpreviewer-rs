# Scene seed, fence presence and known host-message parts

The verified mapped-image route now reaches actual PreviewsServicesUI implementation, UUID899379ca784a339c9c7385c74b587018. Five mapped segments total110,488 bytes. All224 bytes across7 dlsym probes match their segment/container bytes, independent LLVM disassembly and imported Ghidra memory. Three container faults are rejected. Initial and extended owned loads produced the same container hash in these observations; this is not universal live-data stability. Raw Apple code stays local.

## Source-backed distinctions

SceneUpdateSeed.init() is a24-byte global load/add1/store/result/return sequence. Its ADD has no overflow trap or atomic operation. Fresh owned module data contains initial0; no private Swift constructor was invoked. This supports a wrapping64-bit successor algorithm for this build, not concurrent uniqueness or cross-process persistence. Rust SceneSeedCounter explicitly takes caller-owned last state; callers must supply appropriate domain ownership/synchronization. It is not a hidden replacement for the native process-global service.

SceneMessage.timing gets the optional fence: present maps to fenced, absent maps to async. The selected getter performs no wait. Separate require/requireNil helpers reject absent/present fences respectively; their names do not establish signal state. Three independent Swift reflection domains and literal strings corroborate timing/message tags, including Swift long-string pointer bias correction.

HostToShellMessage construction requires seed for preferencesResolved and permits an optional fence. confirmReadyForDisplayAfterSceneResize consumes no payload and forbids a fence. hardwareEvent forbids a fence, extracts eventData and invokes native event decoding. Source string names do not prove that a frame became visible, a GPU completed or an event was dispatched.

## Original implementation

scene_timing adds SceneUpdateSeed, explicit caller-owned wrapping counter, timing classification, message-kind/fence-presence policy and a partial decode_parts API for preferencesResolved and resize confirmation. Inputs are separate typed tag/payload/token parts; no native envelope/transport encoding is invented. Generic F owns its lifetime. Hardware-event decoding returns UnsupportedHardwareEvent after fence-policy validation; arbitrary bytes are not silently accepted as a native event. Foundation numeric/null/error parity remains unqualified.

Sixty-five Rust tests pass (61 prior+4 new). Controls cover signed64 wrap endpoints, repeated successor sequence, exact timing tags, preserved opaque fence token, forbidden fence/unsupported-event/missing-seed/type/unknown-tag errors and original token-drop accounting. Success keeps its token until message drop; failure paths drop each owned test token once. These are portable adapter ownership tests, not native Mach/IOSurface/kernel release or no-later-effect receipts.

Bounded owned mapper runs use30s compile/15s process deadlines and call no resolved private Swift entrypoint; dlopen can run library initializers. Independent metadata.py validates mapped field domains/initial state; verify_container.py checks mapping/probes and corruptions. Private Swift ABI prototypes are never invoked. The first byte-check response parser failure and rejected/expired acquisition cleanup are retained. No competing native writer ran. Final publication checks use the exclusive controller lock; future long analysis must retain a keeper for its full duration.

The current raw profile uses local ASLR addresses/rebased data and omits LINKEDIT. Generated outputs are Apple bytes and stay local. No Xcode MCP/bridge, Xcode attach/injection/restart/workspace, Apple re-signing/protection change or user-process termination occurred. Prior evidence seal/members were reverified; REA session closed. Both milestones and native R1/R2/capture remain open.

Next inspect UVHardwareEvent Objective-C runtime methods and eventData encoding/validation through safe owned objects; qualify actual dispatch separately. Then correlate update seeds/fence operations with actual surface publication and captured frames. Do not equate a seed with an IOSurface ID or fence presence with completion.
