use canvas_core::{human_readable_error::{extract_encoded_with,ARCHIVE_KEY},payload_codec::Value as V,transport_reply::{select_reply_projecting_error,LazyReply,ReplyError}};
use std::collections::BTreeMap;
fn main(){
 let info=BTreeMap::from([(ARCHIVE_KEY.into(),V::Dictionary(BTreeMap::from([("owned".into(),V::Integer(i64::MIN))])))]);
 assert_eq!(extract_encoded_with(&info,|fields|Ok::<_,()>(fields["owned"].clone())),Some(V::Integer(i64::MIN)));
 assert_eq!(extract_encoded_with::<(),_>(&info,|_|Err("rejected")),None);
 assert_eq!(extract_encoded_with::<(),()>(&BTreeMap::new(),|_|panic!()),None);
 let payload=LazyReply::Serialized(vec![]);
 assert_eq!(select_reply_projecting_error(Some(payload.clone()),Some(17),|_|->String{panic!()}),Ok(payload));
 assert_eq!(select_reply_projecting_error(None,Some(17),|x|x.to_string()),Err(ReplyError::Remote("17".into())));
 println!("PASS: WASI archive extraction, suppressed decode error, missing-key bypass and deferred reply projection");
}
