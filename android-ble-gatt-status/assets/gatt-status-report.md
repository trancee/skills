# Android GATT status investigation: [scope]

## Failure signature
- callback/API stage:
- raw status decimal/hex and newState:
- attempt/epoch/elapsed time:
- Android/API/OEM/device/peripheral firmware:
- permission/adapter/bond/process/background state:
- scan age/RSSI/connectable and reproduction rate:

## Reproduction matrix
| phone/build | peer/firmware | direct/auto | app state | condition | attempts/failures | result |
|---|---|---|---|---|---:|---|
| | | | | | | |

## Timeline and ownership
- connection owner/invariants:
- callback GATT/epoch matching:
- cleanup/close evidence:
- retry eligibility/backoff/budget/cancellation:

## Evidence
- app events/logcat/dumpsys/AppOps:
- HCI/air/peer trace:
- control app/phone/peripheral results:
- missing evidence:

## Classification
- class: local precondition | security | peer/RF/controller | GATT stage | platform/OEM | unknown
- supported cause/mitigation:
- rejected hypotheses:
- confidence and limitations:

## Verification
- deterministic/virtual-time tests:
- compile/static checks:
- real-device repeats after change:
