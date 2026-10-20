//! Bounded scalar/container subset of observed libxpc version-5 message bodies.
//! Excludes Mach headers, descriptors, rights, OOL storage and unobserved tags.
//! Strict padding/UTF-8/duplicate policies are original fail-closed choices.
use crate::settings_xpc::XpcValue;
use std::collections::BTreeMap;
const MAX_BYTES: usize = 64 * 1024 * 1024;
const MAX_NODES: usize = 100_000;
const MAX_DEPTH: usize = 64;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Header,
    Version,
    Bounds,
    Limit,
    Padding,
    Text,
    DuplicateKey,
    Tag(u32),
    Container,
    Trailing,
}
struct Reader<'a> {
    bytes: &'a [u8],
    pos: usize,
    nodes: usize,
}
impl<'a> Reader<'a> {
    fn take(&mut self, n: usize) -> Result<&'a [u8], Error> {
        let end = self.pos.checked_add(n).ok_or(Error::Bounds)?;
        let x = self.bytes.get(self.pos..end).ok_or(Error::Bounds)?;
        self.pos = end;
        Ok(x)
    }
    fn word(&mut self) -> Result<u32, Error> {
        Ok(u32::from_le_bytes(self.take(4)?.try_into().unwrap()))
    }
    fn pad(&mut self) -> Result<(), Error> {
        let n = (4 - self.pos % 4) % 4;
        if self.take(n)?.iter().any(|b| *b != 0) {
            return Err(Error::Padding);
        }
        Ok(())
    }
    fn key(&mut self) -> Result<String, Error> {
        let tail = self.bytes.get(self.pos..).ok_or(Error::Bounds)?;
        let n = tail.iter().position(|b| *b == 0).ok_or(Error::Text)?;
        let s = std::str::from_utf8(self.take(n)?)
            .map_err(|_| Error::Text)?
            .to_owned();
        self.take(1)?;
        self.pad()?;
        Ok(s)
    }
    fn value(&mut self, depth: usize) -> Result<XpcValue, Error> {
        use XpcValue::*;
        self.nodes += 1;
        if depth > MAX_DEPTH || self.nodes > MAX_NODES {
            return Err(Error::Limit);
        }
        match self.word()? {
            0x2000 => match self.word()? {
                0 => Ok(Bool(false)),
                1 => Ok(Bool(true)),
                _ => Err(Error::Container),
            },
            0x3000 => Ok(Int64(i64::from_le_bytes(self.take(8)?.try_into().unwrap()))),
            0x4000 => Ok(UInt64(u64::from_le_bytes(
                self.take(8)?.try_into().unwrap(),
            ))),
            0x8000 => {
                let n = self.word()? as usize;
                let b = self.take(n)?.to_vec();
                self.pad()?;
                Ok(Data(b))
            }
            0x9000 => {
                let n = self.word()? as usize;
                let b = self.take(n)?;
                if b.last() != Some(&0) || b[..b.len().saturating_sub(1)].contains(&0) {
                    return Err(Error::Text);
                }
                let s = std::str::from_utf8(&b[..b.len() - 1])
                    .map_err(|_| Error::Text)?
                    .to_owned();
                self.pad()?;
                Ok(String(s))
            }
            tag @ (0xe000 | 0xf000) => {
                let length = self.word()? as usize;
                let end = self.pos.checked_add(length).ok_or(Error::Bounds)?;
                if end > self.bytes.len() || length < 4 {
                    return Err(Error::Bounds);
                }
                let count = self.word()? as usize;
                if count > MAX_NODES - self.nodes {
                    return Err(Error::Limit);
                }
                let mut array = Vec::new();
                let mut dict = BTreeMap::new();
                for _ in 0..count {
                    let key = if tag == 0xf000 {
                        Some(self.key()?)
                    } else {
                        None
                    };
                    let value = self.value(depth + 1)?;
                    if self.pos > end {
                        return Err(Error::Container);
                    }
                    if let Some(key) = key {
                        if dict.insert(key, value).is_some() {
                            return Err(Error::DuplicateKey);
                        }
                    } else {
                        array.push(value);
                    }
                }
                if self.pos != end {
                    return Err(Error::Container);
                }
                Ok(if tag == 0xf000 {
                    Dictionary(dict)
                } else {
                    Array(array)
                })
            }
            tag => Err(Error::Tag(tag)),
        }
    }
}
pub fn decode_body(bytes: &[u8]) -> Result<XpcValue, Error> {
    if bytes.len() > MAX_BYTES {
        return Err(Error::Limit);
    }
    if bytes.get(..4) != Some(b"CPX@") {
        return Err(Error::Header);
    }
    let mut r = Reader {
        bytes,
        pos: 4,
        nodes: 0,
    };
    if r.word()? != 5 {
        return Err(Error::Version);
    }
    let value = r.value(0)?;
    if r.pos != bytes.len() {
        return Err(Error::Trailing);
    }
    Ok(value)
}
struct Writer {
    bytes: Vec<u8>,
    nodes: usize,
}
impl Writer {
    fn append(&mut self, b: &[u8]) -> Result<(), Error> {
        if b.len() > MAX_BYTES - self.bytes.len() {
            return Err(Error::Limit);
        }
        self.bytes.extend_from_slice(b);
        Ok(())
    }
    fn word(&mut self, n: u32) -> Result<(), Error> {
        self.append(&n.to_le_bytes())
    }
    fn pad(&mut self) -> Result<(), Error> {
        while self.bytes.len() % 4 != 0 {
            self.append(&[0])?;
        }
        Ok(())
    }
    fn value(&mut self, v: &XpcValue, depth: usize) -> Result<(), Error> {
        use XpcValue::*;
        self.nodes += 1;
        if depth > MAX_DEPTH || self.nodes > MAX_NODES {
            return Err(Error::Limit);
        }
        match v {
            Bool(b) => {
                self.word(0x2000)?;
                self.word(u32::from(*b))?;
            }
            Int64(n) => {
                self.word(0x3000)?;
                self.append(&n.to_le_bytes())?;
            }
            UInt64(n) => {
                self.word(0x4000)?;
                self.append(&n.to_le_bytes())?;
            }
            Data(b) => {
                self.word(0x8000)?;
                self.word(u32::try_from(b.len()).map_err(|_| Error::Limit)?)?;
                self.append(b)?;
                self.pad()?;
            }
            String(s) => {
                if s.contains('\0') {
                    return Err(Error::Text);
                }
                self.word(0x9000)?;
                self.word(
                    u32::try_from(s.len().checked_add(1).ok_or(Error::Limit)?)
                        .map_err(|_| Error::Limit)?,
                )?;
                self.append(s.as_bytes())?;
                self.append(&[0])?;
                self.pad()?;
            }
            Array(_) | Dictionary(_) => {
                self.word(if matches!(v, Array(_)) {
                    0xe000
                } else {
                    0xf000
                })?;
                let size_pos = self.bytes.len();
                self.word(0)?;
                let start = self.bytes.len();
                match v {
                    Array(a) => {
                        self.word(u32::try_from(a.len()).map_err(|_| Error::Limit)?)?;
                        for x in a {
                            self.value(x, depth + 1)?;
                        }
                    }
                    Dictionary(d) => {
                        self.word(u32::try_from(d.len()).map_err(|_| Error::Limit)?)?;
                        for (key, value) in d {
                            if key.contains('\0') {
                                return Err(Error::Text);
                            }
                            self.append(key.as_bytes())?;
                            self.append(&[0])?;
                            self.pad()?;
                            self.value(value, depth + 1)?;
                        }
                    }
                    _ => unreachable!(),
                }
                let size = u32::try_from(self.bytes.len() - start).map_err(|_| Error::Limit)?;
                self.bytes[size_pos..size_pos + 4].copy_from_slice(&size.to_le_bytes());
            }
        }
        Ok(())
    }
}
/// Canonical sorted-key encoding of this observed subset; native dictionary
/// iteration order is not promised. No endpoint or attachment is synthesized.
pub fn encode_body(value: &XpcValue) -> Result<Vec<u8>, Error> {
    let mut w = Writer {
        bytes: b"CPX@\x05\0\0\0".to_vec(),
        nodes: 0,
    };
    w.value(value, 0)?;
    Ok(w.bytes)
}
