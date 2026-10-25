use canvas_core::{binary_plist,binary_plist_writer::encode_dictionary,payload_codec::Value as V,service_property_list::ServicePropertyList as P,service_reply_error::ServiceReplyError,service_response::send_service_response_binary,settings_xpc::XpcValue as X};
use std::{collections::BTreeMap,path::Path};
fn main() {
    let arg=std::env::args().nth(1).unwrap();let dir=Path::new(&arg);std::fs::create_dir_all(dir).unwrap();
    let request=BTreeMap::from([("owned.request".into(),V::String("request 🪨".into())),("sequence".into(),V::Integer(17))]);std::fs::write(dir.join("request.data"),encode_dictionary(&request).unwrap()).unwrap();
    for (name,source) in [("normal","tools/re/rust/canvas-core/tests/fixtures/service-property-list/nested.wire-data"),("error","tools/re/rust/canvas-core/tests/fixtures/service-wire-reply/remote-error.wire-data")] {
        let V::Dictionary(fields)=binary_plist::decode(&std::fs::read(source).unwrap()).unwrap() else {panic!()};
        let (payload,error)=if name=="error" {(None,Some(ServiceReplyError::recognize(&fields).unwrap()))} else {(Some(P::Dictionary(fields)),None)};
        let mut wire=BTreeMap::new();assert_eq!(send_service_response_binary(true,payload,error,&mut wire,Some,|_|()),Some(()));
        let X::Data(bytes)=wire.remove("data").unwrap() else {panic!()};std::fs::write(dir.join(format!("{name}.data")),bytes).unwrap();
    }
    for (name,payload) in [("empty",P::Dictionary(BTreeMap::from([("unsupported".into(),V::Null)]))),("malformed",P::Data(b"owned invalid plist".to_vec()))] {
        let mut wire=BTreeMap::new();assert_eq!(send_service_response_binary(true,Some(payload),None::<()>,&mut wire,|_|None,|_|()),Some(()));let X::Data(bytes)=wire.remove("data").unwrap() else {panic!()};std::fs::write(dir.join(format!("{name}.data")),bytes).unwrap();
    }
}
