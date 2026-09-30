# Stripe patterns and singularities

## Stripe patterns

The trajectories are the isolines of a stripe pattern [Knöppel et al. 2015] computed by geometry-central:
a function on the mesh whose gradient follows the directional field, with a prescribed frequency.
Its isolines at multiples of 2π run across the field, one spacing apart.

* The frequency is `1 / spacing`, with `spacing = 2 * stitch_height / stretch_wale`, the pre-strain along the wale.
* The field is a line field: `v` and `-v` are the same direction.

Measured on `2part_remesh2`, the median distance between neighbouring trajectories is within 0.1 % of
the spacing for stitch heights from 1.5 to 6.

<!-- TODO: figure, field and stripes -->

## Singularities

Where the field cannot be followed with evenly spaced stripes, the pattern has **singularities**:
triangles where the stripe value, followed around the triangle, comes back shifted by 2π.
One more stripe enters on one side than leaves on the other, so one trajectory ends there.

geometry-central's own linking through these triangles pairs the crossings by their order along the edges,
and could join a trajectory to its neighbour (a U-turn) or step it onto the next stripe.
compas\_knit links them in `src/cpp_stripes/src/singularities.cpp` instead:

1. every crossing on the triangle's edges is labelled with its stripe level;
2. going around the triangle the labels jump by the singularity index at a seam, and each of the three edges
   can be taken as the seam;
3. for each choice, crossings with the same label are joined, and the choice whose links run most across the
   field is kept;
4. the crossing left without a partner is where a trajectory ends.

Next to a singularity the remaining trajectory shifts sideways by up to half a spacing, where two stripes merge into one.

<!-- TODO: before/after figure -->
<!-- ![](../.gitbook/assets/singularity-before-after.png) -->

## Checking the result

[`check_trajectories`](../api/stripes.md#check_trajectories) reports segments running within 60° of the field,
which a correct trajectory should cross. `generate_stripes` runs it by default.

## References

* F. Knöppel, K. Crane, U. Pinkall, P. Schröder. *Stripe Patterns on Surfaces.* ACM Transactions on Graphics 34(4), 2015.
* [geometry-central](https://geometry-central.net), `surface/stripe_patterns`.
* [shrink-morph](https://github.com/DavidJourdan/shrink-morph), where the C++ extraction was ported from.
