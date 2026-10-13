# Security staging: move original source files out of public Git

**2026-10-13: DRAFT – do not merge this quarantine proposal until source availability and rebuild are solved.**

A private-secret-based read-only audit found protected-name fingerprint matches in publicly tracked original source files. In ÖST explicit numeric ages under 18 were also observed in both source databases. In Gotaleden original startlist files include an Email field. No individual identity is documented here.

This security proposal **removes `data/archive/ost-results-2018-2026.sqlite.gz` and `data/derived/ost-analysis-2018-2026.sqlite.gz`.** from the current Git tree. It does **not** delete old commits, forks, history or caches. It also does not create an access-controlled backup.

**Required before merge or production rebuild:**
1. Provision a dedicated private source repository or secure encrypted object storage, with correct access rights and backup retention.
2. Transfer the exact original source bytes to this private location; verify checksums, complete file listing, independent copy and restoration. Do not use public GitHub Releases, Pages, public workflow logs or public Actions artifacts for confidential originals.
3. Refactor ingestion/build/test workflows so credentials only read from secure secrets, source is fetched to temporary workspace, and build/publication fails closed without it.
4. Prove that rebuilt `docs/data` are sanitized with the private suppression registry and that functionality/analytics are unchanged.
5. Merge quarantine and verify current public Git tree has none of the raw sources. Coordinate Git history rewrite/cache purge and assess whether incident notification is necessary.
6. Do not reset source-derived checksums or golden master snapshots just to make failing tests appear green.

See the incident tracking issue: https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys/issues/74.

Removing original source files from a PR branch is not itself a privacy fix for the deployed public repository. Current `main` remains exposed until a controlled release, and old history must be handled separately.
