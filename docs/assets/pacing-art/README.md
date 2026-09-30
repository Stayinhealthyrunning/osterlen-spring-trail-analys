# Pacing profile artwork integration

The two-segment pacing chart reserves two responsive, transparent background layers on `.two-segment-pacing-chart`:

- `--pacing-art-coast` for the start-to-Bengtemölla side
- `--pacing-art-inland` for the Bengtemölla-to-finish side

When the final watercolor artwork is available, add optimized transparent WebP or AVIF files in this directory and assign them from `style.css`, for example:

```css
.two-segment-pacing-chart {
  --pacing-art-coast: url("pacing-art/coast-to-bengtemolla.webp");
  --pacing-art-inland: url("pacing-art/bengtemolla-to-christinehof.webp");
}
```

Keep both layers decorative, low contrast and free of text. The chart, the Bengtemölla control label and all analytical values must remain readable without the artwork. The current inline route motifs are temporary orientation marks and can be removed once approved final assets are connected here.
