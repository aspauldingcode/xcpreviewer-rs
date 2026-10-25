use canvas_core::{remote_error::{RemoteErrorLeaf,Error,Severity},human_readable_error::{extract_encoded_with,ARCHIVE_KEY},payload_codec::Value as V,binary_plist,binary_plist_writer};use std::collections::BTreeMap;
fn main(){
 let mut f=BTreeMap::from([("errorType".into(),V::String("leaf".into()))]);let v=RemoteErrorLeaf::from_dictionary(&f).unwrap();assert!(v.is_potential_crash);assert!(!v.is_native);assert_eq!(v.error_type_description,"[Remote] Unknown Error");
 f.insert("options".into(),V::Integer(i64::MAX));f.insert("severity".into(),V::String("info".into()));f.insert("errorTypeDescription".into(),V::String("owned 🪨".into()));
 let v=extract_encoded_with(&BTreeMap::from([(ARCHIVE_KEY.into(),V::Dictionary(f.clone()))]),RemoteErrorLeaf::from_dictionary).unwrap();assert_eq!(v.options,Some(i64::MAX));assert_eq!(v.severity,Some(Severity::Info));
 let V::Dictionary(f2)=binary_plist::decode(&binary_plist_writer::encode_dictionary(&v.to_dictionary()).unwrap()).unwrap()else{panic!()};assert_eq!(RemoteErrorLeaf::from_dictionary(&f2).unwrap(),v);
 f.insert("errorType".into(),V::String("wrapper".into()));assert_eq!(RemoteErrorLeaf::from_dictionary(&f),Err(Error::UnsupportedWrapper));
 println!("PASS: WASI remote leaf defaults, signed options, severity, archive extraction, binary round-trip and wrapper rejection");
}
