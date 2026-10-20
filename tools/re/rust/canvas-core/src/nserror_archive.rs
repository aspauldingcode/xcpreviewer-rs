//! Bounded canonical NSError bplist17 profile measured through BSXPCCoder.
//! Supports domain/code and nil archived userInfo only. This is not a general
//! bplist17/object-graph decoder; opaque completion archives remain preserved.
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
