# Reconstruction QA

Before a reconstructed route enters a Loppanalys dataset, QA checks that resolved segments have evidence, unresolved gaps stay explicit, adjacent geometry connects, loop courses close, distance is compared with nominal and observed values, mandatory controls occur in sequence, hard contradictions are absent, and the course version/year scope is recorded.

Distance deviation is a warning signal, not proof. Trail races can differ from nominal distance and GPS measurements vary.

The QA result travels with the route artifact so a frontend can distinguish source geometry, validated reconstruction, candidate reconstruction and unresolved geometry. Reconstructed geometry must never be represented as organizer GPX.
