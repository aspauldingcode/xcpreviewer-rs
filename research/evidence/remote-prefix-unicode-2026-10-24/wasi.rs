use canvas_core::{remote_error::RemoteErrorLeaf,payload_codec::Value as V};use std::collections::BTreeMap;
fn main(){for suffix in ["owned","🪨","\u{301}x","\u{fe0f}x","\u{200d}x","\u{903}x","\nx"]{
 let title=format!("[Remote] {suffix}");let rejected=["\u{301}x","\u{fe0f}x","\u{200d}x","\u{903}x"].contains(&suffix);
 let fields=BTreeMap::from([("errorType".into(),V::String("leaf".into())),("errorTypeDescription".into(),V::String(title.clone()))]);
 assert_eq!(RemoteErrorLeaf::from_dictionary(&fields).unwrap().error_type_description,if rejected{format!("[Remote] {title}")}else{title});
}println!("PASS: WASI Swift remote-prefix combining/variation/ZWJ/spacing-mark corrections; emoji and control boundaries retained");}
