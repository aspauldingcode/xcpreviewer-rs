//! Bounded canonical NSError bplist17 profile measured through BSXPCCoder.
//! ArchivedNSError retains the canonical nil-userInfo profile. NSErrorDetails
//! adds string-valued dictionary decoding. Arbitrary object graphs remain
//! unsupported and original completion archive bytes stay preserved.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ArchivedNSError { pub domain: String, pub code: i64 }
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error { Bounds, Limit, Profile, Integer, Utf16, UnsupportedUserInfo, NonCanonical }
const MAX_BYTES: usize = 1024 * 1024;
const MAX_DOMAIN_UNITS: usize = 65536;
struct Cursor<'a> { bytes: &'a [u8], at: usize }
impl<'a> Cursor<'a> {
    fn take(&mut self, n: usize) -> Result<&'a [u8], Error> {
        let end = self.at.checked_add(n).ok_or(Error::Bounds)?;
        let value = self.bytes.get(self.at..end).ok_or(Error::Bounds)?;
        self.at = end; Ok(value)
    }
    fn expect(&mut self, value: &[u8]) -> Result<(), Error> {
        if self.take(value.len())? == value { Ok(()) } else { Err(Error::Profile) }
    }
    fn integer(&mut self) -> Result<i64, Error> {
        let width = match self.take(1)?[0] { 0x11 => 1, 0x12 => 2, 0x14 => 4, 0x18 => 8, _ => return Err(Error::Integer) };
        let mut value = [0u8; 8]; value[..width].copy_from_slice(self.take(width)?);
        Ok(i64::from_le_bytes(value))
    }
    fn end_offset(&mut self) -> Result<(), Error> {
        self.expect(&[0xd0])?;
        let mut raw = [0u8; 8]; raw.copy_from_slice(self.take(8)?);
        if u64::from_le_bytes(raw) != self.bytes.len().checked_sub(1).ok_or(Error::Bounds)? as u64 { return Err(Error::Profile) }
        Ok(())
    }
}
fn integer(out: &mut Vec<u8>, value: i64) {
    let width = if value < 0 || value > u32::MAX as i64 { 8 } else if value > u16::MAX as i64 { 4 } else if value > u8::MAX as i64 { 2 } else { 1 };
    out.push(0x10 | width as u8); out.extend_from_slice(&value.to_le_bytes()[..width]);
}
impl ArchivedNSError {
    pub fn decode(bytes: &[u8]) -> Result<Self, Error> {
        if bytes.len() > MAX_BYTES { return Err(Error::Limit) }
        let mut c = Cursor { bytes, at: 0 };
        c.expect(b"bplist17")?; c.end_offset()?; c.expect(b"\x74bsx\0")?; c.end_offset()?;
        c.expect(b"\x77$class\0\x78NSError\0\x77NSCode\0")?;
        let code = c.integer()?; c.expect(b"\x79NSDomain\0")?;
        let tag = c.take(1)?[0];
        let units = match tag { 0x60..=0x6e => (tag & 15) as usize, 0x6f => usize::try_from(c.integer()?).map_err(|_| Error::Limit)?, _ => return Err(Error::Profile) };
        if units > MAX_DOMAIN_UNITS { return Err(Error::Limit) }
        let raw = c.take(units.checked_mul(2).ok_or(Error::Bounds)?)?;
        let utf16: Vec<u16> = raw.chunks_exact(2).map(|v| u16::from_le_bytes([v[0], v[1]])).collect();
        let domain = String::from_utf16(&utf16).map_err(|_| Error::Utf16)?;
        c.expect(b"\x7bNSUserInfo\0")?;
        if c.take(1)? != [0xe0] { return Err(Error::UnsupportedUserInfo) }
        if c.at != bytes.len() { return Err(Error::Profile) }
        let value = Self { domain, code };
        if value.encode()? != bytes { return Err(Error::NonCanonical) }
        Ok(value)
    }
    /// Re-encode only this observed canonical field order and nil-userInfo profile.
    pub fn encode(&self) -> Result<Vec<u8>, Error> {
        let units: Vec<u16> = self.domain.encode_utf16().collect();
        if units.len() > MAX_DOMAIN_UNITS { return Err(Error::Limit) }
        let mut out = b"bplist17".to_vec(); out.push(0xd0); let outer = out.len(); out.extend_from_slice(&[0; 8]);
        out.extend_from_slice(b"\x74bsx\0\xd0"); let inner = out.len(); out.extend_from_slice(&[0; 8]);
        out.extend_from_slice(b"\x77$class\0\x78NSError\0\x77NSCode\0"); integer(&mut out, self.code);
        out.extend_from_slice(b"\x79NSDomain\0");
        if units.len() < 15 { out.push(0x60 | units.len() as u8) } else { out.push(0x6f); integer(&mut out, units.len() as i64) }
        for u in units { out.extend_from_slice(&u.to_le_bytes()) }
        out.extend_from_slice(b"\x7bNSUserInfo\0\xe0");
        if out.len() > MAX_BYTES { return Err(Error::Limit) }
        let end = (out.len() - 1) as u64; out[outer..outer+8].copy_from_slice(&end.to_le_bytes()); out[inner..inner+8].copy_from_slice(&end.to_le_bytes()); Ok(out)
    }
}


/// Selected string-valued NSError userInfo. Original archive ownership and
/// byte order belong to the completion; this is a semantic decoding view.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NSErrorDetails {
    pub error: ArchivedNSError,
    pub user_info: std::collections::BTreeMap<String, String>,
}
struct DetailCursor<'a> {
    inner: Cursor<'a>,
    strings: std::collections::BTreeMap<usize, String>,
    decoded_bytes: usize,
}
impl DetailCursor<'_> {
    fn charge(&mut self, bytes: usize) -> Result<(), Error> {
        self.decoded_bytes = self.decoded_bytes.checked_add(bytes).ok_or(Error::Limit)?;
        if self.decoded_bytes > MAX_BYTES { return Err(Error::Limit) }
        Ok(())
    }
    fn container(&mut self, tag: u8) -> Result<usize, Error> {
        self.inner.expect(&[tag])?;
        let mut raw = [0u8; 8]; raw.copy_from_slice(self.inner.take(8)?);
        let end = usize::try_from(u64::from_le_bytes(raw)).map_err(|_| Error::Bounds)?;
        if end >= self.inner.bytes.len() || end + 1 < self.inner.at { return Err(Error::Bounds) }
        Ok(end)
    }
    fn text(&mut self) -> Result<String, Error> {
        let start = self.inner.at;
        let tag = self.inner.take(1)?[0];
        let value = match tag {
            0x60..=0x6f => {
                let units = if tag == 0x6f { usize::try_from(self.inner.integer()?).map_err(|_| Error::Limit)? } else { (tag & 15) as usize };
                if units > MAX_DOMAIN_UNITS { return Err(Error::Limit) }
                let bytes = self.inner.take(units.checked_mul(2).ok_or(Error::Bounds)?)?;
                let units: Vec<_> = bytes.chunks_exact(2).map(|v| u16::from_le_bytes([v[0],v[1]])).collect();
                String::from_utf16(&units).map_err(|_| Error::Utf16)?
            }
            0x70..=0x7f => {
                let count = if tag == 0x7f { usize::try_from(self.inner.integer()?).map_err(|_| Error::Limit)? } else { (tag & 15) as usize };
                if count == 0 || count > MAX_DOMAIN_UNITS { return Err(Error::Limit) }
                let bytes = self.inner.take(count)?;
                if bytes.last() != Some(&0) || !bytes[..count-1].is_ascii() { return Err(Error::Profile) }
                String::from_utf8(bytes[..count-1].to_vec()).map_err(|_| Error::Profile)?
            }
            0x81 | 0x82 | 0x84 | 0x88 => {
                let mut raw = [0u8;8]; let width = (tag & 15) as usize;
                raw[..width].copy_from_slice(self.inner.take(width)?);
                let offset = usize::try_from(u64::from_le_bytes(raw)).map_err(|_| Error::Bounds)?;
                if offset >= start { return Err(Error::Profile) }
                let value = self.strings.get(&offset).cloned().ok_or(Error::Profile)?;
                self.charge(value.len())?; return Ok(value);
            }
            _ => return Err(Error::UnsupportedUserInfo),
        };
        if self.strings.len() >= 4096 { return Err(Error::Limit) }
        self.charge(value.len())?; self.strings.insert(start, value.clone()); Ok(value)
    }
    fn expected_text(&mut self, text: &str) -> Result<(), Error> {
        if self.text()? == text { Ok(()) } else { Err(Error::Profile) }
    }
    fn array(&mut self) -> Result<Vec<String>, Error> {
        let end = self.container(0xa0)?; let mut values = Vec::new();
        while self.inner.at <= end {
            if values.len() >= 1024 { return Err(Error::Limit) }
            values.push(self.text()?);
        }
        if self.inner.at != end + 1 { return Err(Error::Profile) }
        Ok(values)
    }
}
impl NSErrorDetails {
    /// Decode the observed NSDictionary NS.keys/NS.objects string profile.
    /// Numeric/nested objects and arbitrary graph references remain unsupported.
    pub fn decode(bytes: &[u8]) -> Result<Self, Error> {
        if bytes.len() > MAX_BYTES { return Err(Error::Limit) }
        let mut c = DetailCursor { inner: Cursor { bytes, at: 0 }, strings: Default::default(), decoded_bytes: 0 };
        c.inner.expect(b"bplist17")?;
        let outer = c.container(0xd0)?; c.expected_text("bsx")?;
        let object_end = c.container(0xd0)?;
        if outer + 1 != bytes.len() || object_end != outer { return Err(Error::Profile) }
        c.expected_text("$class")?; c.expected_text("NSError")?;
        c.expected_text("NSCode")?; let code = c.inner.integer()?;
        c.expected_text("NSDomain")?; let domain = c.text()?;
        c.expected_text("NSUserInfo")?;
        let mut user_info = std::collections::BTreeMap::new();
        if c.inner.bytes.get(c.inner.at) == Some(&0xe0) { c.inner.take(1)?; }
        else {
            let end = c.container(0xd0)?;
            c.expected_text("$class")?; c.expected_text("NSDictionary")?;
            c.expected_text("NS.keys")?; let keys = c.array()?;
            c.expected_text("NS.objects")?; let values = c.array()?;
            if keys.len() != values.len() || c.inner.at != end + 1 { return Err(Error::Profile) }
            for (key,value) in keys.into_iter().zip(values) {
                if user_info.insert(key,value).is_some() { return Err(Error::Profile) }
            }
        }
        if c.inner.at != bytes.len() { return Err(Error::Profile) }
        Ok(Self { error: ArchivedNSError { domain, code }, user_info })
    }
}
