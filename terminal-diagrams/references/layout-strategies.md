# Layout strategies

## Linear process

Place nodes along the requested axis. Keep gaps wide enough for arrowheads and labels. Use top-to-bottom when labels are long or canvas width is tight.

## Tree or hierarchy

Center each parent over its children, reserve a horizontal bus row, then drop one vertical branch per child. Ensure sibling subtrees do not overlap. Prefer separate repeated boxes over a dense crossing mesh.

## DAG or service topology

Assign ranks from sources to sinks, order nodes within each rank to reduce crossings, then route edges through dedicated corridors. If routing becomes ambiguous, split into control-plane/data-plane or request/response panels.

## Cycle or state machine

Lay out the primary progression monotonically and route return/error edges around the outside with labels. Arrowheads must make cycles explicit.

## Data schema

Use table-like boxes for entities: header, field/type rows, optional key markers. Route relationships from stable side ports. Keep cardinality text adjacent to the appropriate endpoint.

## Canvas assembly

Treat the canvas as display cells. Place all plain node rows first, then connectors, then labels, then ANSI. Collision precedence is semantic: node border/label > arrowhead > connector label > line. Any collision at a higher priority requires rerouting rather than overwriting.

Rectangular component rows must match that component’s width. Whole-canvas rows may differ for a sparse diagram; right-pad them only when the output contract requires a rectangular canvas.
