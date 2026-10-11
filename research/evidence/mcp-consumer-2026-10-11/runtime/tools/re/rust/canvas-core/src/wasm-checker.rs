// Appended only to owned checker modules. Full expected allocation is independent.
static EXPECTED: &[u8; 16384] = include_bytes!("EXPECTED_PATH");
#[no_mangle]
pub extern "C" fn verify(mutation: u32) -> u32 {
    if mutation > 4 { return u32::MAX; }
    if render(STRIDE) != STRIDE * HEIGHT { return u32::MAX; }
    if mutation == 4 && render(0) != 0 { return u32::MAX; }
    // Safety: same single-threaded, import-free storage boundary as render.
    let actual = unsafe { &mut *STORAGE.0.get() };
    match mutation { 1 => actual[0] ^= 1, 2 => actual[PADDING] ^= 1,
                     3 => actual[16383] ^= 1, _ => {} }
    actual.iter().zip(EXPECTED.iter()).filter(|(a,b)|a!=b).count() as u32
}
