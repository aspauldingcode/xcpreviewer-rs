Operator transcriptions; failures retained without native retry:

- Initial scanner finite-positive control failed normally and optimized because the ID parser omitted role-prefixed first metadata. Original scanner retained. Corrected parser reports syntax candidates only, explicitly including value/metadata serialization ambiguity; six methods passed before UI.
- Native original guard failed with duplicate index30. First native tree line was five tabs plus `30 row (selected)`; later CUA supplemental `Selected:` line was one tab plus identical text. This is not a duplicated AX tree node. No Refresh/title/input followed the guard error; only passive screenshot/empty receipt diagnostics and exact cleanup.
- Initial Python normalizer test expected a stripped trailing newline, while the implementation correctly preserved the tree substring. Original test retained; expectation corrected. No native replay used the new normalizer.

- While tightening the exact known footer, an unescaped apostrophe in single-quoted Python/JS strings caused syntax failures. All four failing source variants are retained as .quote-failed.txt; escaping corrected before frozen verification. No native execution used these files.
