//! Original typed CrashReport property-list adapter recovered from shipped code.
//! Strict Value typing and error labels are reconstruction policy. UUID creation
//! requires caller-provided entropy; no platform fallback or fixed ID is hidden.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
type Fields = BTreeMap<String, Value>;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    Range(&'static str),
    InvalidUuid,
    EntropyRequired,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Uuid(pub [u8; 16]);
impl Uuid {
    pub fn parse(text: &str) -> Result<Self, Error> {
        let b = text.as_bytes();
        if b.len() != 36 {
            return Err(Error::InvalidUuid);
        }
        let mut out = [0; 16];
        let mut pos = 0;
        fn hex(b: u8) -> Result<u8, Error> {
            match b {
                b'0'..=b'9' => Ok(b - b'0'),
                b'a'..=b'f' => Ok(b - b'a' + 10),
                b'A'..=b'F' => Ok(b - b'A' + 10),
                _ => Err(Error::InvalidUuid),
            }
        }
        for (i, byte) in out.iter_mut().enumerate() {
            if [4, 6, 8, 10].contains(&i) {
                if b[pos] != b'-' {
                    return Err(Error::InvalidUuid);
                }
                pos += 1;
            }
            *byte = (hex(b[pos])? << 4) | hex(b[pos + 1])?;
            pos += 2;
        }
        Ok(Self(out))
    }
    pub fn canonical(self) -> String {
        let digits = b"0123456789ABCDEF";
        let mut out = String::with_capacity(36);
        for (i, b) in self.0.iter().enumerate() {
            if [4, 6, 8, 10].contains(&i) {
                out.push('-');
            }
            out.push(digits[(b >> 4) as usize] as char);
            out.push(digits[(b & 15) as usize] as char);
        }
        out
    }
    pub fn v4_from_entropy(mut bytes: [u8; 16]) -> Self {
        bytes[6] = (bytes[6] & 15) | 0x40;
        bytes[8] = (bytes[8] & 63) | 0x80;
        Self(bytes)
    }
}
fn dictionary<'a>(v: &'a Value, k: &'static str) -> Result<&'a Fields, Error> {
    match v {
        Value::Dictionary(d) => Ok(d),
        _ => Err(Error::Type(k)),
    }
}
fn required<'a>(d: &'a Fields, k: &'static str) -> Result<&'a Value, Error> {
    d.get(k).ok_or(Error::Missing(k))
}
fn string(v: &Value, k: &'static str) -> Result<String, Error> {
    match v {
        Value::String(s) => Ok(s.clone()),
        _ => Err(Error::Type(k)),
    }
}
fn integer(v: &Value, k: &'static str) -> Result<i64, Error> {
    match v {
        Value::Integer(n) => Ok(*n),
        _ => Err(Error::Type(k)),
    }
}
fn strings(v: &Value, k: &'static str) -> Result<Vec<String>, Error> {
    match v {
        Value::Array(a) => a.iter().map(|v| string(v, k)).collect(),
        _ => Err(Error::Type(k)),
    }
}
fn optional<T>(
    d: &Fields,
    k: &'static str,
    f: impl FnOnce(&Value, &'static str) -> Result<T, Error>,
) -> Result<Option<T>, Error> {
    d.get(k).map(|v| f(v, k)).transpose()
}
fn put_optional<T>(d: &mut Fields, k: &str, v: &Option<T>, f: impl FnOnce(&T) -> Value) {
    if let Some(v) = v {
        d.insert(k.into(), f(v));
    }
}
fn string_array(v: &[String]) -> Value {
    Value::Array(v.iter().cloned().map(Value::String).collect())
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CrashImage {
    pub uuid: String,
    pub arch: Option<String>,
    pub base: i64,
    pub path: Option<String>,
    pub name: Option<String>,
}
impl CrashImage {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = dictionary(v, "image")?;
        Ok(Self {
            uuid: string(required(d, "uuid")?, "uuid")?,
            arch: optional(d, "arch", string)?,
            base: integer(required(d, "base")?, "base")?,
            path: optional(d, "path", string)?,
            name: optional(d, "name", string)?,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut d = Fields::new();
        d.insert("uuid".into(), Value::String(self.uuid.clone()));
        put_optional(&mut d, "arch", &self.arch, |v| Value::String(v.clone()));
        d.insert("base".into(), Value::Integer(self.base));
        put_optional(&mut d, "path", &self.path, |v| Value::String(v.clone()));
        put_optional(&mut d, "name", &self.name, |v| Value::String(v.clone()));
        Value::Dictionary(d)
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CrashFrame {
    pub image_index: i64,
    pub image_offset: i64,
    pub symbol: Option<String>,
    pub symbol_location: Option<i64>,
    pub source_file: Option<String>,
    pub source_line: Option<i64>,
}
impl CrashFrame {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = dictionary(v, "frame")?;
        Ok(Self {
            image_index: integer(required(d, "imageIndex")?, "imageIndex")?,
            image_offset: integer(required(d, "imageOffset")?, "imageOffset")?,
            symbol: optional(d, "symbol", string)?,
            symbol_location: optional(d, "symbolLocation", integer)?,
            source_file: optional(d, "sourceFile", string)?,
            source_line: optional(d, "sourceLine", integer)?,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut d = Fields::new();
        d.insert("imageIndex".into(), Value::Integer(self.image_index));
        d.insert("imageOffset".into(), Value::Integer(self.image_offset));
        put_optional(&mut d, "symbol", &self.symbol, |v| Value::String(v.clone()));
        put_optional(&mut d, "symbolLocation", &self.symbol_location, |v| {
            Value::Integer(*v)
        });
        put_optional(&mut d, "sourceFile", &self.source_file, |v| {
            Value::String(v.clone())
        });
        put_optional(&mut d, "sourceLine", &self.source_line, |v| {
            Value::Integer(*v)
        });
        Value::Dictionary(d)
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CrashTermination {
    pub flags: Option<i64>,
    pub code: Option<i64>,
    pub namespace: Option<String>,
    pub details: Option<Vec<String>>,
    pub indicator: Option<String>,
    pub by_proc: Option<String>,
    pub by_pid: Option<i64>,
    pub reasons: Option<Vec<String>>,
}
impl CrashTermination {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = dictionary(v, "termination")?;
        Ok(Self {
            flags: optional(d, "flags", integer)?,
            code: optional(d, "code", integer)?,
            namespace: optional(d, "namespace", string)?,
            details: optional(d, "details", strings)?,
            indicator: optional(d, "indicator", string)?,
            by_proc: optional(d, "byProc", string)?,
            by_pid: optional(d, "byPid", integer)?,
            reasons: optional(d, "reasons", strings)?,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut d = Fields::new();
        put_optional(&mut d, "flags", &self.flags, |v| Value::Integer(*v));
        put_optional(&mut d, "code", &self.code, |v| Value::Integer(*v));
        put_optional(&mut d, "namespace", &self.namespace, |v| {
            Value::String(v.clone())
        });
        put_optional(&mut d, "details", &self.details, |v| string_array(v));
        put_optional(&mut d, "indicator", &self.indicator, |v| {
            Value::String(v.clone())
        });
        put_optional(&mut d, "byProc", &self.by_proc, |v| {
            Value::String(v.clone())
        });
        put_optional(&mut d, "byPid", &self.by_pid, |v| Value::Integer(*v));
        put_optional(&mut d, "reasons", &self.reasons, |v| string_array(v));
        Value::Dictionary(d)
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct CrashReport {
    pub id: Uuid,
    pub name: String,
    pub bug_type: String,
    pub pid: i32,
    pub time: f64,
    pub asi: Option<BTreeMap<String, Vec<String>>>,
    pub termination: Option<CrashTermination>,
    pub images: Vec<CrashImage>,
    pub frames: Vec<CrashFrame>,
    pub log_file_path: Option<String>,
}
impl CrashReport {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        Self::decode_with_entropy(v, &mut || Err(Error::EntropyRequired))
    }
    /// Native absence generates a new UUID. Portable callers provide the entropy
    /// boundary explicitly; it is invoked once, only when the id key is absent.
    pub fn decode_with_entropy(
        v: &Value,
        entropy: &mut impl FnMut() -> Result<[u8; 16], Error>,
    ) -> Result<Self, Error> {
        let d = dictionary(v, "crashReport")?;
        let id = match d.get("id") {
            Some(v) => Uuid::parse(&string(v, "id")?)?,
            None => Uuid::v4_from_entropy(entropy()?),
        };
        let name = string(required(d, "name")?, "name")?;
        let bug_type = string(required(d, "bugType")?, "bugType")?;
        let pid =
            i32::try_from(integer(required(d, "pid")?, "pid")?).map_err(|_| Error::Range("pid"))?;
        let time = match required(d, "time")? {
            Value::Date(t) => *t,
            _ => return Err(Error::Type("time")),
        };
        let asi = optional(d, "asi", |v, k| {
            dictionary(v, k)?
                .iter()
                .map(|(key, v)| Ok((key.clone(), strings(v, k)?)))
                .collect()
        })?;
        let termination = optional(d, "termination", |v, _| CrashTermination::decode(v))?;
        let images = match required(d, "images")? {
            Value::Array(a) => a.iter().map(CrashImage::decode).collect::<Result<_, _>>()?,
            _ => return Err(Error::Type("images")),
        };
        let frames = match required(d, "frames")? {
            Value::Array(a) => a.iter().map(CrashFrame::decode).collect::<Result<_, _>>()?,
            _ => return Err(Error::Type("frames")),
        };
        let log_file_path = optional(d, "logFilePath", string)?;
        Ok(Self {
            id,
            name,
            bug_type,
            pid,
            time,
            asi,
            termination,
            images,
            frames,
            log_file_path,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut d = Fields::from([
            ("id".into(), Value::String(self.id.canonical())),
            ("name".into(), Value::String(self.name.clone())),
            ("bugType".into(), Value::String(self.bug_type.clone())),
            ("pid".into(), Value::Integer(i64::from(self.pid))),
            ("time".into(), Value::Date(self.time)),
            (
                "images".into(),
                Value::Array(self.images.iter().map(CrashImage::to_value).collect()),
            ),
            (
                "frames".into(),
                Value::Array(self.frames.iter().map(CrashFrame::to_value).collect()),
            ),
        ]);
        put_optional(&mut d, "asi", &self.asi, |values| {
            Value::Dictionary(
                values
                    .iter()
                    .map(|(k, v)| (k.clone(), string_array(v)))
                    .collect(),
            )
        });
        put_optional(
            &mut d,
            "termination",
            &self.termination,
            CrashTermination::to_value,
        );
        put_optional(&mut d, "logFilePath", &self.log_file_path, |v| {
            Value::String(v.clone())
        });
        Value::Dictionary(d)
    }
}
