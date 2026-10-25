//! Bounded bplist00 reader for preview payload input.
//! Format reference: Apple's CF ForFoundationOnly.h marker/trailer definitions.
//! Limits and rejection policy are original reconstruction choices, not claims
//! about Foundation's acceptance of malformed or non-preview property lists.
use crate::payload_codec::{self, BitmapDescription, SelectableRegion, Value};
use crate::render_payload::RenderPayload;
use std::collections::{BTreeMap, BTreeSet};

const MAX_NODES: usize = 100_000;
const MAX_BYTES: usize = 64 * 1024 * 1024;
const MAX_DEPTH: usize = 64;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Header,
    Trailer,
    Bounds,
    Unsupported(u8),
    Text,
    Cycle,
    Limit,
    DictionaryKey,
    DuplicateKey,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PayloadError {
    Plist(Error),
    Fields(payload_codec::DecodeError),
}

pub fn decode_render_payload_binary(
    bytes: &[u8],
) -> Result<RenderPayload<BitmapDescription, SelectableRegion>, PayloadError> {
    let value = decode(bytes).map_err(PayloadError::Plist)?;
    payload_codec::decode_render_payload(&value).map_err(PayloadError::Fields)
}
fn number(bytes: &[u8]) -> Result<usize, Error> {
    let n = bytes.iter().fold(0u64, |n, b| (n << 8) | u64::from(*b));
    usize::try_from(n).map_err(|_| Error::Bounds)
}
pub fn decode(bytes: &[u8]) -> Result<Value, Error> {
    if bytes.get(..8) != Some(b"bplist00") {
        return Err(Error::Header);
    }
    let trailer_start = bytes.len().checked_sub(32).ok_or(Error::Trailer)?;
    if trailer_start < 8 {
        return Err(Error::Trailer);
    }
    let t = &bytes[trailer_start..];
    let offset_width = usize::from(t[6]);
    let ref_width = usize::from(t[7]);
    if !(1..=8).contains(&offset_width) || !(1..=8).contains(&ref_width) {
        return Err(Error::Trailer);
    }
    let count = number(&t[8..16])?;
    let top = number(&t[16..24])?;
    let table = number(&t[24..32])?;
    if count == 0 || top >= count {
        return Err(Error::Trailer);
    }
    if count > MAX_NODES {
        return Err(Error::Limit);
    }
    let table_end = count
        .checked_mul(offset_width)
        .and_then(|n| table.checked_add(n))
        .ok_or(Error::Bounds)?;
    if table < 8 || table_end != trailer_start {
        return Err(Error::Trailer);
    }
    let offsets = bytes[table..table_end]
        .chunks_exact(offset_width)
        .map(number)
        .collect::<Result<Vec<_>, _>>()?;
    if offsets.iter().any(|p| *p < 8 || *p >= table) {
        return Err(Error::Bounds);
    }
    Reader {
        bytes,
        table,
        ref_width,
        offsets,
        path: BTreeSet::new(),
        nodes: MAX_NODES,
        copied: 0,
    }
    .object(top, 0)
}
struct Reader<'a> {
    bytes: &'a [u8],
    table: usize,
    ref_width: usize,
    offsets: Vec<usize>,
    path: BTreeSet<usize>,
    nodes: usize,
    copied: usize,
}
impl Reader<'_> {
    fn span(&self, start: usize, length: usize) -> Result<&[u8], Error> {
        let end = start.checked_add(length).ok_or(Error::Bounds)?;
        if end > self.table {
            return Err(Error::Bounds);
        }
        self.bytes.get(start..end).ok_or(Error::Bounds)
    }
    fn charge(&mut self, length: usize) -> Result<(), Error> {
        self.copied = self.copied.checked_add(length).ok_or(Error::Limit)?;
        if self.copied > MAX_BYTES {
            return Err(Error::Limit);
        }
        Ok(())
    }
    fn length(&self, start: usize, small: u8) -> Result<(usize, usize), Error> {
        if small < 15 {
            return Ok((usize::from(small), start));
        }
        let marker = self.span(start, 1)?[0];
        if marker >> 4 != 1 || marker & 15 > 3 {
            return Err(Error::Unsupported(marker));
        }
        let size = 1usize << (marker & 15);
        let length = number(self.span(start + 1, size)?)?;
        Ok((length, start + 1 + size))
    }
    fn reference(&self, start: usize) -> Result<usize, Error> {
        let id = number(self.span(start, self.ref_width)?)?;
        if id >= self.offsets.len() {
            return Err(Error::Bounds);
        }
        Ok(id)
    }
    fn object(&mut self, id: usize, depth: usize) -> Result<Value, Error> {
        if depth > MAX_DEPTH || self.nodes == 0 {
            return Err(Error::Limit);
        }
        self.nodes -= 1;
        if !self.path.insert(id) {
            return Err(Error::Cycle);
        }
        let result = self.contents(id, depth);
        self.path.remove(&id);
        result
    }
    fn contents(&mut self, id: usize, depth: usize) -> Result<Value, Error> {
        let start = *self.offsets.get(id).ok_or(Error::Bounds)?;
        let marker = self.span(start, 1)?[0];
        let kind = marker >> 4;
        let small = marker & 15;
        let payload = start + 1;
        match marker {
            0x00 => return Ok(Value::Null),
            0x08 => return Ok(Value::Boolean(false)),
            0x09 => return Ok(Value::Boolean(true)),
            0x33 => {
                return Ok(Value::Date(f64::from_be_bytes(
                    self.span(payload, 8)?.try_into().unwrap(),
                )))
            }
            _ => (),
        }
        match kind {
            1 if small <= 3 => {
                let raw = self.span(payload, 1usize << small)?;
                let n = raw.iter().fold(0u64, |n, b| (n << 8) | u64::from(*b));
                Ok(Value::Integer(n as i64))
            }
            1 if small == 4 => {
                let raw = self.span(payload, 16)?;
                if raw[..8].iter().any(|byte| *byte != 0) {
                    return Err(Error::Unsupported(marker));
                }
                let number = u64::from_be_bytes(raw[8..].try_into().unwrap());
                Ok(if number <= i64::MAX as u64 {
                    Value::Integer(number as i64)
                } else {
                    Value::Unsigned(number)
                })
            }
            2 => match small {
                2 => Ok(Value::Real(
                    f32::from_be_bytes(self.span(payload, 4)?.try_into().unwrap()) as f64,
                )),
                3 => Ok(Value::Real(f64::from_be_bytes(
                    self.span(payload, 8)?.try_into().unwrap(),
                ))),
                _ => Err(Error::Unsupported(marker)),
            },
            4..=6 => {
                let (length, base) = self.length(payload, small)?;
                let size = length
                    .checked_mul(if kind == 6 { 2 } else { 1 })
                    .ok_or(Error::Bounds)?;
                self.span(base, size)?;
                self.charge(
                    size.checked_mul(if kind == 6 { 2 } else { 1 })
                        .ok_or(Error::Limit)?,
                )?;
                let raw = self.span(base, size)?;
                match kind {
                    4 => Ok(Value::Data(raw.to_vec())),
                    5 => {
                        if !raw.is_ascii() {
                            return Err(Error::Text);
                        }
                        Ok(Value::String(
                            String::from_utf8(raw.to_vec()).map_err(|_| Error::Text)?,
                        ))
                    }
                    _ => {
                        let units = raw
                            .chunks_exact(2)
                            .map(|c| u16::from_be_bytes([c[0], c[1]]))
                            .collect::<Vec<_>>();
                        Ok(Value::String(
                            String::from_utf16(&units).map_err(|_| Error::Text)?,
                        ))
                    }
                }
            }
            0xa | 0xd => {
                let (length, base) = self.length(payload, small)?;
                if length > self.nodes {
                    return Err(Error::Limit);
                }
                let refs = length
                    .checked_mul(if kind == 0xd { 2 } else { 1 })
                    .ok_or(Error::Bounds)?;
                self.span(base, refs.checked_mul(self.ref_width).ok_or(Error::Bounds)?)?;
                if kind == 0xa {
                    let mut values = Vec::with_capacity(length);
                    for i in 0..length {
                        let reference = self.reference(base + i * self.ref_width)?;
                        values.push(self.object(reference, depth + 1)?);
                    }
                    Ok(Value::Array(values))
                } else {
                    let mut values = BTreeMap::new();
                    for i in 0..length {
                        let key_ref = self.reference(base + i * self.ref_width)?;
                        let val_ref = self.reference(base + (length + i) * self.ref_width)?;
                        let key = match self.object(key_ref, depth + 1)? {
                            Value::String(s) => s,
                            _ => return Err(Error::DictionaryKey),
                        };
                        if values.contains_key(&key) {
                            return Err(Error::DuplicateKey);
                        }
                        let value = self.object(val_ref, depth + 1)?;
                        values.insert(key, value);
                    }
                    Ok(Value::Dictionary(values))
                }
            }
            _ => Err(Error::Unsupported(marker)),
        }
    }
}
