//! Decode one local preview from stdin; emit the original bounded display packet.
use std::io::{Read, Write};
fn main() {
    let result = (|| -> Result<(), String> {
        let mut input = Vec::new();
        std::io::stdin()
            .take(64 * 1024 * 1024 + 1)
            .read_to_end(&mut input)
            .map_err(|e| e.to_string())?;
        let output = canvas_core::browser_frame::frame_packet(&input)?;
        std::io::stdout()
            .write_all(&output)
            .map_err(|e| e.to_string())?;
        Ok(())
    })();
    if let Err(error) = result {
        eprintln!("{error}");
        std::process::exit(1)
    }
}
