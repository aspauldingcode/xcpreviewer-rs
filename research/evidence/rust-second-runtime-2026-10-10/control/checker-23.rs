//! Owned single-threaded, import-free WASM ABI. Configuration supplied at build time.
#![no_std]
#![no_main]
#[path = "/Users/8amps/xcpreviewer-rs/research/runs/20261011T061257Z-primary-live-wasm-swap-1defb692/source/tools/re/rust/canvas-core/src/contract.rs"]
mod contract;
use core::cell::UnsafeCell;
use contract::{FrameSpec, ALLOCATION, render_primary};
struct Storage(UnsafeCell<[u8; ALLOCATION]>);
// Safety: module has no imports, threads or shared memory. Calls cannot reenter;
// only render borrows storage, and the borrow ends before returning to the host.
unsafe impl Sync for Storage {}
static STORAGE: Storage = Storage(UnsafeCell::new([0xc3; ALLOCATION]));
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
#[no_mangle]
pub extern "C" fn capacity() -> u32 { ALLOCATION as u32 }
#[no_mangle]
pub extern "C" fn pixels() -> u32 { STORAGE.0.get() as u32 }
#[no_mangle]
pub extern "C" fn render(stride: u32) -> u32 {
    // Safety: see Storage; no host callback occurs while this reference exists.
    let output = unsafe { &mut *STORAGE.0.get() };
    render_primary(FrameSpec { width: 13, height: 7, stride },
                   [7, 7, 1], false, output).unwrap_or(0) as u32
}
// Appended only to owned checker modules. Full expected allocation is independent.
static EXPECTED: &[u8; 16384] = include_bytes!("/Users/8amps/xcpreviewer-rs/research/runs/20261011T061257Z-primary-live-wasm-swap-1defb692/output/rust-wasm/inputs/bd9bd4fcedf2ee4139566437f0d80f486ff048c37e7df6afe8cd4b0ae4deff62.raw");
#[no_mangle]
pub extern "C" fn verify(mutation: u32) -> u32 {
    if mutation > 4 { return u32::MAX; }
    if render(64) != 64 * 7 { return u32::MAX; }
    if mutation == 4 && render(0) != 0 { return u32::MAX; }
    // Safety: same single-threaded, import-free storage boundary as render.
    let actual = unsafe { &mut *STORAGE.0.get() };
    match mutation { 1 => actual[0] ^= 1, 2 => actual[52] ^= 1,
                     3 => actual[16383] ^= 1, _ => {} }
    actual.iter().zip(EXPECTED.iter()).filter(|(a,b)|a!=b).count() as u32
}
