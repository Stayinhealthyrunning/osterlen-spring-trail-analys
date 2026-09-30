# Pacing profile artwork integration

The current approved transparent watercolor asset is `docs/assets/ost-pacing-watercolor.webp`. It is attached through `.bengtemolla-pacing article::before` in `style.css`, which keeps the image decorative, responsive and behind the analytical chart.

Replace that optimized WebP at the same path when a revised approved artwork is supplied, or update the single CSS URL if the asset name changes. Preserve the pseudo-element as the integration layer, keep `pointer-events: none`, and verify the mobile opacity/position override. The chart, Bengtemölla control label and all analytical values must remain fully readable without the artwork.