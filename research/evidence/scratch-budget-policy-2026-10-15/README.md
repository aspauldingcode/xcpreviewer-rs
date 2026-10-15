# Research-only scratch accounting proposal

Retained-output logical cap remains512MiB. Only three exact CAS paths at exact16/8/1GiB logical extents receive scratch designation; independent total allocated storage cap remains512MiB. Partial shapes count as retained output. This is reported filesystem allocation, not exclusive physical usage or a hard quota.

Caller must supply a fresh controller-owned run directory, keep scratch out of accepted/exported artifacts, bound traversal time independently, and reject incomplete or concurrently invalidated observations. No controller integration or native build executed. Nine tests and an independent unreadable-subtree regression pass; retained actual corpus discriminates prior logical-cap failure from small allocated storage. Original fail-open traversal finding is preserved in review.json.
