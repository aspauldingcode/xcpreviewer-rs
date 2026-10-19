1. Native-session admission: ownedRegistry is not defined before any UI call. Original failed call began binding the new context through the previously assumed registry; no workspace opened.
2. Pure conditional-var witness: object existed in same call, identifier undefined on next call. Other factory/guard/Xcode bindings were still present, so whole-runtime reset is not established.
3. Proposed repeated top-level self initializer: duplicate bind unexpectedly succeeded; explicit guard threw registry was reset. This alternative is rejected.
4. Nullish global property and then stricter hasOwn property controls rejected duplicate binding across calls. Strict proposal also refuses corrupt existing slots in standard VM tests; no corrected native session attempted.
