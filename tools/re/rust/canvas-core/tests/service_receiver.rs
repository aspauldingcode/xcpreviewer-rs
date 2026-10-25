use canvas_core::{
    service_property_list::ServicePropertyList,
    service_receiver::{
        prepare_service_dictionary, ServiceMessageReceiver, ServiceReceiverMessage,
    },
    settings_xpc::XpcValue,
};
use std::{cell::Cell, collections::BTreeMap, rc::Rc};
fn wire(bytes: &[u8]) -> BTreeMap<String, XpcValue> {
    BTreeMap::from([("data".into(), XpcValue::Data(bytes.to_vec()))])
}
#[derive(Default)]
struct Receiver {
    one_way: Vec<ServicePropertyList>,
    requests: Vec<(ServicePropertyList, u32)>,
}
impl ServiceMessageReceiver<u32> for Receiver {
    fn receive(&mut self, message: ServicePropertyList) {
        self.one_way.push(message);
    }
    fn receive_with_reply(&mut self, message: ServicePropertyList, reply: u32) {
        self.requests.push((message, reply));
    }
}

#[test]
fn reply_capability_selects_receiver_method_without_parsing_or_remote_error_recognition() {
    for bytes in [
        include_bytes!("fixtures/service-property-list/nested.wire-data").as_slice(),
        include_bytes!("fixtures/service-property-list/malformed.wire-data").as_slice(),
        include_bytes!("fixtures/service-property-list/array_root.wire-data").as_slice(),
        include_bytes!("fixtures/service-wire-reply/remote-error.wire-data").as_slice(),
    ] {
        let calls = Cell::new(0);
        let mut receiver = Receiver::default();
        let mut fields = wire(bytes);
        let message = prepare_service_dictionary(&fields, || {
            calls.set(calls.get() + 1);
            None::<u32>
        })
        .unwrap();
        assert_eq!(
            message,
            ServiceReceiverMessage::OneWay(ServicePropertyList::Data(bytes.to_vec()))
        );
        message.dispatch_to(Some(&mut receiver));
        let message = prepare_service_dictionary(&fields, || {
            calls.set(calls.get() + 1);
            Some(17_u32)
        })
        .unwrap();
        fields.clear();
        assert_eq!(
            message,
            ServiceReceiverMessage::WithReply {
                message: ServicePropertyList::Data(bytes.to_vec()),
                reply: 17
            }
        );
        message.dispatch_to(Some(&mut receiver));
        assert_eq!(calls.get(), 2);
        assert_eq!(
            receiver.one_way,
            [ServicePropertyList::Data(bytes.to_vec())]
        );
        assert_eq!(
            receiver.requests,
            [(ServicePropertyList::Data(bytes.to_vec()), 17)]
        );
    }
}

#[test]
fn rejected_wire_never_creates_reply_capability_or_calls_receiver() {
    for fields in [
        BTreeMap::new(),
        wire(&[]),
        BTreeMap::from([("data".into(), XpcValue::String("wrong type".into()))]),
    ] {
        let message = prepare_service_dictionary(&fields, || -> Option<u32> {
            panic!("wire initializer rejects before create_reply")
        });
        assert_eq!(message, None);
    }
}

#[test]
fn missing_receiver_drops_only_local_reply_capture_without_synthesizing_response() {
    struct Reply(Rc<Cell<usize>>);
    impl Drop for Reply {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1);
        }
    }
    let drops = Rc::new(Cell::new(0));
    let creations = Cell::new(0);
    let message = prepare_service_dictionary(&wire(b"owned nonempty"), || {
        creations.set(creations.get() + 1);
        Some(Reply(drops.clone()))
    })
    .unwrap();
    assert_eq!(creations.get(), 1);
    assert_eq!(drops.get(), 0);
    message.dispatch_to(None);
    assert_eq!(drops.get(), 1);
}

#[test]
fn receiver_can_retain_reply_capability_for_later_response() {
    struct Deferred {
        message: Option<ServicePropertyList>,
        reply: Option<Box<dyn FnOnce(u32)>>,
    }
    impl ServiceMessageReceiver<Box<dyn FnOnce(u32)>> for Deferred {
        fn receive(&mut self, _: ServicePropertyList) {
            panic!("expected request");
        }
        fn receive_with_reply(
            &mut self,
            message: ServicePropertyList,
            reply: Box<dyn FnOnce(u32)>,
        ) {
            self.message = Some(message);
            self.reply = Some(reply);
        }
    }
    let completed = Rc::new(Cell::new(0_u32));
    let captured = completed.clone();
    let mut receiver = Deferred {
        message: None,
        reply: None,
    };
    let message = prepare_service_dictionary(&wire(b"owned request"), || {
        Some(Box::new(move |value| captured.set(value)) as Box<dyn FnOnce(u32)>)
    })
    .unwrap();
    message.dispatch_to(Some(&mut receiver));
    assert_eq!(completed.get(), 0);
    assert_eq!(
        receiver.message,
        Some(ServicePropertyList::Data(b"owned request".to_vec()))
    );
    receiver.reply.take().unwrap()(17);
    assert_eq!(completed.get(), 17);
    // The FnOnce capability is this caller's choice, not native multiplicity evidence.
}
