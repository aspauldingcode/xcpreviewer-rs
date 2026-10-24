//! Scoped forwarding value codec, recovered from MessagingHost.
//! No process selection, transport send, execution or completion is performed.
use crate::{agent_message_kind::AgentMessageKind, binary_plist, payload_codec::Value};
use std::collections::BTreeMap;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PreviewContentDomain { View, Widget, Complication }
impl PreviewContentDomain {
    pub const fn as_str(self) -> &'static str { match self { Self::View=>"application",Self::Widget=>"widget",Self::Complication=>"complication" } }
    pub fn from_raw(s:&str)->Option<Self> { match s { "application"=>Some(Self::View),"widget"=>Some(Self::Widget),"complication"=>Some(Self::Complication),_=>None } }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PreviewOrientation { Portrait, PortraitUpsideDown, LandscapeLeft, LandscapeRight }
impl PreviewOrientation {
    pub const fn as_str(self)->&'static str { match self {Self::Portrait=>"portrait",Self::PortraitUpsideDown=>"portraitUpsideDown",Self::LandscapeLeft=>"landscapeLeft",Self::LandscapeRight=>"landscapeRight"} }
    pub fn from_raw(s:&str)->Option<Self> { match s {"portrait"=>Some(Self::Portrait),"portraitUpsideDown"=>Some(Self::PortraitUpsideDown),"landscapeLeft"=>Some(Self::LandscapeLeft),"landscapeRight"=>Some(Self::LandscapeRight),_=>None} }
}
#[derive(Clone, Debug, PartialEq)]
pub struct ForwardPayload {
    pub message_type: AgentMessageKind,
    pub message_payload: Value,
    pub pid: i32,
    pub content_domain: Option<PreviewContentDomain>,
    pub preview_interface_orientation: Option<PreviewOrientation>,
    pub scene_identifier: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error { Plist(binary_plist::Error), Missing(&'static str), Type(&'static str), Range(&'static str), Unsupported(&'static str) }
fn text<'a>(v:&'a Value,k:&'static str)->Result<&'a str,Error> { if let Value::String(s)=v {Ok(s)} else {Err(Error::Type(k))} }
impl ForwardPayload {
    /// Strict portable scalar types. Foundation coercion and explicit-null parity
    /// remain unqualified. A missing orientation normalizes to Some(Portrait).
    pub fn decode(v:&Value)->Result<Self,Error> {
        let Value::Dictionary(d)=v else {return Err(Error::Type("forwardPayload"));};
        let get=|k:&'static str| d.get(k).ok_or(Error::Missing(k));
        let message_type=AgentMessageKind::from_raw(text(get("messageType")?,"messageType")?).ok_or(Error::Unsupported("messageType"))?;
        let message_payload=get("messagePayload")?.clone();
        let pid=match get("pid")? {Value::Integer(n)=>i32::try_from(*n).map_err(|_|Error::Range("pid"))?,_=>return Err(Error::Type("pid"))};
        let content_domain=d.get("previewContextType").map(|v| {PreviewContentDomain::from_raw(text(v,"previewContextType")?).ok_or(Error::Unsupported("previewContextType"))}).transpose()?;
        let preview_interface_orientation=Some(match d.get("previewInterfaceOrientation") {
            None=>PreviewOrientation::Portrait,
            Some(v)=>PreviewOrientation::from_raw(text(v,"previewInterfaceOrientation")?).ok_or(Error::Unsupported("previewInterfaceOrientation"))?,
        });
        let scene_identifier=d.get("sceneIdentifier").map(|v|text(v,"sceneIdentifier").map(str::to_owned)).transpose()?;
        Ok(Self {message_type,message_payload,pid,content_domain,preview_interface_orientation,scene_identifier})
    }
    pub fn decode_binary(bytes:&[u8])->Result<Self,Error> {Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)}
    pub fn to_value(&self)->Value {
        let mut d=BTreeMap::from([("messageType".into(),Value::String(self.message_type.as_str().into())),("messagePayload".into(),self.message_payload.clone()),("pid".into(),Value::Integer(i64::from(self.pid)))]);
        if let Some(v)=self.content_domain {d.insert("previewContextType".into(),Value::String(v.as_str().into()));}
        if let Some(v)=self.preview_interface_orientation {d.insert("previewInterfaceOrientation".into(),Value::String(v.as_str().into()));}
        if let Some(v)=&self.scene_identifier {d.insert("sceneIdentifier".into(),Value::String(v.clone()));}
        Value::Dictionary(d)
    }
}
