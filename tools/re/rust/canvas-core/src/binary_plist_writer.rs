//! Original deterministic bplist00 writer for bounded portable values.
//! Output is validated semantically against public Foundation, not claimed
//! byte-identical to its serializer. Null and nonfinite numbers are excluded.
use crate::payload_codec::Value;
use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Limits {
    pub objects: usize,
    pub bytes: usize,
    pub depth: usize,
}
impl Default for Limits {
    fn default() -> Self {
        Self {
            objects: 100_000,
            bytes: 64 * 1024 * 1024,
            depth: 64,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Limit,
    Null,
    NonFinite,
}

enum Node<'a> {
    Boolean(bool),
    Integer(i64),
    Real(f64),
    Date(f64),
    Data(&'a [u8]),
    String(&'a str),
    Array(Vec<usize>),
    Dictionary(Vec<usize>, Vec<usize>),
}
struct Builder<'a> {
    nodes: Vec<Node<'a>>,
    limits: Limits,
}
impl<'a> Builder<'a> {
    fn slot(&mut self, depth: usize) -> Result<usize, Error> {
        if depth > self.limits.depth || self.nodes.len() >= self.limits.objects {
            return Err(Error::Limit);
        }
        let id = self.nodes.len();
        self.nodes.push(Node::Boolean(false));
        Ok(id)
    }
    fn text(&mut self, value: &'a str, depth: usize) -> Result<usize, Error> {
        // UTF-16 can be smaller than UTF-8; exact output charge is computed later.
        if value.len() > self.limits.bytes.saturating_mul(2) {
            return Err(Error::Limit);
        }
        let id = self.slot(depth)?;
        self.nodes[id] = Node::String(value);
        Ok(id)
    }
    fn dictionary(
        &mut self,
        values: &'a BTreeMap<String, Value>,
        depth: usize,
    ) -> Result<usize, Error> {
        let id = self.slot(depth)?;
        if values.len() > (self.limits.objects - self.nodes.len()) / 2 {
            return Err(Error::Limit);
        }
        let mut keys = Vec::with_capacity(values.len());
        let mut refs = Vec::with_capacity(values.len());
        for (key, value) in values {
            keys.push(self.text(key, depth + 1)?);
            refs.push(self.value(value, depth + 1)?);
        }
        self.nodes[id] = Node::Dictionary(keys, refs);
        Ok(id)
    }
    fn value(&mut self, value: &'a Value, depth: usize) -> Result<usize, Error> {
        if let Value::String(s) = value {
            return self.text(s, depth);
        }
        if let Value::Dictionary(d) = value {
            return self.dictionary(d, depth);
        }
        let id = self.slot(depth)?;
        let node = match value {
            Value::Null => return Err(Error::Null),
            Value::Boolean(v) => Node::Boolean(*v),
            Value::Integer(v) => Node::Integer(*v),
            Value::Real(v) | Value::Date(v) if !v.is_finite() => return Err(Error::NonFinite),
            Value::Real(v) => Node::Real(*v),
            Value::Date(v) => Node::Date(*v),
            Value::Data(v) => {
                if v.len() > self.limits.bytes {
                    return Err(Error::Limit);
                }
                Node::Data(v)
            }
            Value::String(_) => unreachable!(),
            Value::Array(values) => {
                if values.len() > self.limits.objects - self.nodes.len() {
                    return Err(Error::Limit);
                }
                let mut refs = Vec::with_capacity(values.len());
                for value in values {
                    refs.push(self.value(value, depth + 1)?);
                }
                Node::Array(refs)
            }
            Value::Dictionary(_) => unreachable!(),
        };
        self.nodes[id] = node;
        Ok(id)
    }
}
fn width(value: u64) -> usize {
    if value <= 0xff {
        1
    } else if value <= 0xffff {
        2
    } else if value <= 0xffff_ffff {
        4
    } else {
        8
    }
}
fn add(a: usize, b: usize) -> Result<usize, Error> {
    a.checked_add(b).ok_or(Error::Limit)
}
fn mul(a: usize, b: usize) -> Result<usize, Error> {
    a.checked_mul(b).ok_or(Error::Limit)
}
fn prefix(length: usize) -> usize {
    if length < 15 {
        1
    } else {
        2 + width(length as u64)
    }
}
fn size(node: &Node<'_>, refs: usize) -> Result<usize, Error> {
    Ok(match node {
        Node::Boolean(_) => 1,
        Node::Integer(v) => {
            if *v < 0 {
                9
            } else {
                1 + width(*v as u64)
            }
        }
        Node::Real(_) | Node::Date(_) => 9,
        Node::Data(v) => add(prefix(v.len()), v.len())?,
        Node::String(v) => {
            let (length, bytes) = if v.is_ascii() {
                (v.len(), v.len())
            } else {
                let n = v.encode_utf16().count();
                (n, mul(n, 2)?)
            };
            add(prefix(length), bytes)?
        }
        Node::Array(v) => add(prefix(v.len()), mul(v.len(), refs)?)?,
        Node::Dictionary(k, _) => add(prefix(k.len()), mul(mul(k.len(), 2)?, refs)?)?,
    })
}
fn integer(out: &mut Vec<u8>, value: u64, bytes: usize) {
    out.extend_from_slice(&value.to_be_bytes()[8 - bytes..]);
}
fn length(out: &mut Vec<u8>, marker: u8, count: usize) {
    if count < 15 {
        out.push(marker | count as u8);
    } else {
        out.push(marker | 15);
        let bytes = width(count as u64);
        out.push(0x10 | bytes.trailing_zeros() as u8);
        integer(out, count as u64, bytes);
    }
}
fn write(node: &Node<'_>, refs: usize, out: &mut Vec<u8>) {
    match node {
        Node::Boolean(v) => out.push(if *v { 9 } else { 8 }),
        Node::Integer(v) => {
            let bytes = if *v < 0 { 8 } else { width(*v as u64) };
            out.push(0x10 | bytes.trailing_zeros() as u8);
            integer(out, *v as u64, bytes);
        }
        Node::Real(v) => {
            out.push(0x23);
            out.extend_from_slice(&v.to_bits().to_be_bytes());
        }
        Node::Date(v) => {
            out.push(0x33);
            out.extend_from_slice(&v.to_bits().to_be_bytes());
        }
        Node::Data(v) => {
            length(out, 0x40, v.len());
            out.extend_from_slice(v);
        }
        Node::String(v) => {
            if v.is_ascii() {
                length(out, 0x50, v.len());
                out.extend_from_slice(v.as_bytes());
            } else {
                length(out, 0x60, v.encode_utf16().count());
                for unit in v.encode_utf16() {
                    out.extend_from_slice(&unit.to_be_bytes());
                }
            }
        }
        Node::Array(v) => {
            length(out, 0xa0, v.len());
            for id in v {
                integer(out, *id as u64, refs);
            }
        }
        Node::Dictionary(keys, values) => {
            length(out, 0xd0, keys.len());
            for id in keys.iter().chain(values) {
                integer(out, *id as u64, refs);
            }
        }
    }
}
/// Encode finite supported values with hard bounds. Dictionary order follows
/// BTreeMap, objects are not interned, strings use ASCII or UTF-16BE, negative
/// integers use eight bytes and reals/dates retain their f64 bit patterns.
pub fn encode(value: &Value) -> Result<Vec<u8>, Error> {
    encode_with_limits(value, Limits::default())
}
/// Lower caller limits are supported; callers cannot exceed the hard defaults.
/// All object/output sizes are checked before allocating the output buffer.
pub fn encode_with_limits(value: &Value, limits: Limits) -> Result<Vec<u8>, Error> {
    let hard = Limits::default();
    if limits.objects > hard.objects || limits.bytes > hard.bytes || limits.depth > hard.depth {
        return Err(Error::Limit);
    }
    let mut builder = Builder {
        nodes: Vec::new(),
        limits,
    };
    builder.value(value, 0)?;
    finish(builder)
}
/// Borrow a dictionary directly without cloning its potentially large values.
pub fn encode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Vec<u8>, Error> {
    let mut builder = Builder {
        nodes: Vec::new(),
        limits: Limits::default(),
    };
    builder.dictionary(fields, 0)?;
    finish(builder)
}
fn finish(builder: Builder<'_>) -> Result<Vec<u8>, Error> {
    let limits = builder.limits;
    let refs = width((builder.nodes.len() - 1) as u64);
    let mut offsets = Vec::with_capacity(builder.nodes.len());
    let mut table = 8;
    for node in &builder.nodes {
        offsets.push(table);
        table = add(table, size(node, refs)?)?;
        if table > limits.bytes {
            return Err(Error::Limit);
        }
    }
    // Cover the table position as required by the pinned Foundation control.
    let offset_width = width(table as u64);
    let total = add(add(table, mul(offsets.len(), offset_width)?)?, 32)?;
    if total > limits.bytes {
        return Err(Error::Limit);
    }
    let mut out = Vec::with_capacity(total);
    out.extend_from_slice(b"bplist00");
    for node in &builder.nodes {
        write(node, refs, &mut out);
    }
    for offset in offsets {
        integer(&mut out, offset as u64, offset_width);
    }
    out.extend_from_slice(&[0; 6]);
    out.push(offset_width as u8);
    out.push(refs as u8);
    integer(&mut out, builder.nodes.len() as u64, 8);
    integer(&mut out, 0, 8);
    integer(&mut out, table as u64, 8);
    debug_assert_eq!(out.len(), total);
    Ok(out)
}
