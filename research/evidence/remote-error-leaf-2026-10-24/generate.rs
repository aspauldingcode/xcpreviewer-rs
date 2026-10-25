use canvas_core::{remote_error::RemoteErrorLeaf,payload_codec::Value as V,binary_plist_writer};use std::{collections::BTreeMap,path::Path};
fn main(){let arg=std::env::args().nth(1).unwrap();let dir=Path::new(&arg);std::fs::create_dir_all(dir).unwrap();for name in ["default","full","prefixed","empty"]{
 let mut f=BTreeMap::from([("errorType".into(),V::String("leaf".into()))]);
 if name=="full"{for(k,v)in[("errorTypeDescription","owned 🪨"),("highValueTitle",""),("lowValueTitle","low"),("additionalInfo","details\0雪"),("additionalDiagnostics","line\n"),("severity","info")]{f.insert(k.into(),V::String(v.into()));}f.insert("options".into(),V::Integer(i64::MIN));f.insert("isPotentialCrash".into(),V::Boolean(false));f.insert("isNative".into(),V::Boolean(true));}
 if name=="prefixed"{f.insert("errorTypeDescription".into(),V::String("[Remote] stable".into()));f.insert("severity".into(),V::String("error".into()));f.insert("options".into(),V::Integer(i64::MAX));}
 if name=="empty"{f.insert("errorTypeDescription".into(),V::String("".into()));}
 let v=RemoteErrorLeaf::from_dictionary(&f).unwrap();std::fs::write(dir.join(format!("{name}.bplist")),binary_plist_writer::encode_dictionary(&v.to_dictionary()).unwrap()).unwrap();
}}
