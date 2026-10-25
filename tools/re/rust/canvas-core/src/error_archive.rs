//! Bounded canonical human-readable leaf/wrapper archive composition.
//! Tree budgets are original portable limits, not native Foundation limits.
use crate::{payload_codec::Value, remote_error::RemoteErrorLeaf};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ErrorArchive {
    Leaf(RemoteErrorLeaf),
    Wrapper {
        main: Box<Self>,
        underlying: Box<Self>,
    },
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Limits {
    pub nodes: usize,
    pub depth: usize,
}
impl Default for Limits {
    fn default() -> Self {
        Self {
            nodes: 10_000,
            depth: 64,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Limit,
    Missing(&'static str),
    Type(&'static str),
    Leaf(crate::remote_error::Error),
}
fn dictionary<'a>(
    fields: &'a BTreeMap<String, Value>,
    key: &'static str,
) -> Result<&'a BTreeMap<String, Value>, Error> {
    match fields.get(key) {
        None => Err(Error::Missing(key)),
        Some(Value::Dictionary(fields)) => Ok(fields),
        _ => Err(Error::Type(key)),
    }
}
fn charge(nodes: &mut usize, depth: usize, limit: usize) -> Result<(), Error> {
    if *nodes == 0 || depth > limit {
        return Err(Error::Limit);
    }
    *nodes -= 1;
    Ok(())
}
impl ErrorArchive {
    pub fn from_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        Self::from_dictionary_with_limits(fields, Limits::default())
    }
    /// Validate both required child dictionaries before recursively decoding
    /// main, then underlying, following the recovered constructor's order.
    /// The reflected 'cause' case uses the literal wire key 'underlying'.
    /// Leaf coercion/profile limits remain those of RemoteErrorLeaf.
    pub fn from_dictionary_with_limits(
        fields: &BTreeMap<String, Value>,
        limits: Limits,
    ) -> Result<Self, Error> {
        let mut nodes = limits.nodes;
        Self::decode(fields, &mut nodes, 0, limits.depth)
    }
    fn decode(
        fields: &BTreeMap<String, Value>,
        nodes: &mut usize,
        depth: usize,
        max_depth: usize,
    ) -> Result<Self, Error> {
        charge(nodes, depth, max_depth)?;
        if matches!(fields.get("errorType"),Some(Value::String(tag)) if tag=="wrapper") {
            let main = dictionary(fields, "main")?;
            let underlying = dictionary(fields, "underlying")?;
            let main = Self::decode(main, nodes, depth + 1, max_depth)?;
            let underlying = Self::decode(underlying, nodes, depth + 1, max_depth)?;
            Ok(Self::Wrapper {
                main: Box::new(main),
                underlying: Box::new(underlying),
            })
        } else {
            RemoteErrorLeaf::from_dictionary(fields)
                .map(Self::Leaf)
                .map_err(Error::Leaf)
        }
    }
    pub fn to_dictionary(&self) -> Result<BTreeMap<String, Value>, Error> {
        self.to_dictionary_with_limits(Limits::default())
    }
    /// Encode the exact three wrapper keys. Budgets cover archive nodes/depth,
    /// not total string bytes; apply the separate plist writer's byte limits.
    pub fn to_dictionary_with_limits(
        &self,
        limits: Limits,
    ) -> Result<BTreeMap<String, Value>, Error> {
        let mut nodes = limits.nodes;
        self.encode(&mut nodes, 0, limits.depth)
    }
    fn encode(
        &self,
        nodes: &mut usize,
        depth: usize,
        max_depth: usize,
    ) -> Result<BTreeMap<String, Value>, Error> {
        charge(nodes, depth, max_depth)?;
        match self {
            Self::Leaf(leaf) => Ok(leaf.to_dictionary()),
            Self::Wrapper { main, underlying } => Ok(BTreeMap::from([
                ("errorType".into(), Value::String("wrapper".into())),
                (
                    "main".into(),
                    Value::Dictionary(main.encode(nodes, depth + 1, max_depth)?),
                ),
                (
                    "underlying".into(),
                    Value::Dictionary(underlying.encode(nodes, depth + 1, max_depth)?),
                ),
            ])),
        }
    }
    /// Native wrapper getter delegates to the cause, without ORing main flags.
    pub fn is_potential_crash(&self) -> bool {
        let mut node = self;
        while let Self::Wrapper { underlying, .. } = node {
            node = underlying
        }
        let Self::Leaf(leaf) = node else {
            unreachable!()
        };
        leaf.is_potential_crash
    }
    /// Native wrapper getter delegates to main, without ORing cause flags.
    pub fn is_native(&self) -> bool {
        let mut node = self;
        while let Self::Wrapper { main, .. } = node {
            node = main
        }
        let Self::Leaf(leaf) = node else {
            unreachable!()
        };
        leaf.is_native
    }
}
