# Examples

## Vertical service flow

```text
╔══════════════════════════╗
║       API GATEWAY        ║
╠══════════════════════════╣
║ Status: ACTIVE           ║
║ Port:   443              ║
╚════════════╦═════════════╝
             ║
             ▼
┌──────────────────────────┐
│    AUTH SERVICE [v2]     │
└──────────────────────────┘
```

The two boxes are independently rectangular components. Connector-only rows need not equal the box width.

## Labeled horizontal edge

```text
┌──────────────┐                 ┌──────────────┐
│ API Gateway  ├────[ gRPC ]────►│ Auth Service │
└──────────────┘                 └──────────────┘
```

For a production diagram, allocate a longer corridor or put the label on a separate row if the inline label makes the boxes collide.

## Table

```text
┌─────────────────────┬───────────────────────┬──────────────┐
│ Component           │ Endpoint              │ Health       │
├─────────────────────┼───────────────────────┼──────────────┤
│ Billing Engine      │ billing.internal:8080 │ PASS         │
│ Notification Router │ notify.internal:9100  │ WARN         │
└─────────────────────┴───────────────────────┴──────────────┘
```

Use the validator on the actual copied text; editors can alter spaces or Unicode glyphs.
