//! Owned single-threaded, import-free WASM ABI. Configuration supplied at build time.
#![no_std]
#![no_main]
#[path = "/Users/8amps/xcpreviewer-rs/research/runs/20261011T093849Z-primary-live-wasm-swap-6bc05646/source/tools/re/rust/canvas-core/src/contract.rs"]
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
    render_primary(FrameSpec { width: 11, height: 6, stride },
                   [4, 4, 4], false, output).unwrap_or(0) as u32
}
