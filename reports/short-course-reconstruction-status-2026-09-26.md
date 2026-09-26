# Short-course reconstruction status — 2026-09-26

## Trail 5

Current status: validated georeferenced organizer reference geometry; exact persisted centreline still pending repeat digitization.

Known quantitative result:
- organizer raster frame and SWEREF 99 TM controls are archived;
- previous 62-vertex manual centreline measured 5.002 km after affine georeferencing;
- those 62 source pixels were not persisted and therefore cannot be promoted to a reproducible route artifact.

The repository now contains a deterministic persisted-trace georeferencer. The next trace must save source pixel vertices before conversion.

## Trail 13/14

Current status: strong candidate topology.

The eastern corridor is independently constrained by:
- organizer raster;
- current race PM: one lap, Hallamölla midpoint, Verkeån narrow/steep terrain;
- official Hallamöllaleden topology;
- Länsstyrelsen trail map;
- Tomelilla municipal ~2.5 km Alunbruket-east-parking to Hallamölla control;
- OSM named anchors;
- 2023 participant-reported 13.67 km race segment.

The western corridor cross-registers against the organizer Trail 5 raster.

## Geometry acquisition attempts

Raw OSM/Overpass bbox transport remains blocked by the current execution environment, including smaller queries and alternate endpoint attempts. Individual named OSM anchors remain discoverable.

Public Wikiloc pages expose summary/preview evidence but not a reusable raw coordinate chain through the available text interface. No geometry has been inferred from thumbnails.

## Scientific stopping rule

Do not manufacture path vertices from map thumbnails or distance totals. Until exact source pixels are persisted or raw mapped-path geometry becomes available, output status remains reconstructed candidate/reference geometry rather than organizer/race-day GPX.
