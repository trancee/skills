# Versioned value decoders

Decoder result: `Decoded(value, units, fields) | Special(kind) | Unsupported(reason) | Malformed(offset, reason)`, always paired with original copied bytes.

General decoder order:
1. select adopted profile/service/characteristic revision and mandatory errata
2. require minimum flags/header length
3. parse unsigned bytes with explicit little/big endian from specification
4. mask known flags; preserve/report RFU bits without shifting field layout
5. bounds-check before every optional field
6. interpret sentinel/reserved/prohibited values before numeric conversion
7. validate units/ranges and trailing-byte rule
8. return typed result; never throw on remote bytes

IEEE-11073 16-bit SFLOAT uses signed 12-bit mantissa and signed 4-bit base-10 exponent, but first classify raw values: `0x07FF` NaN, `0x0800` NRes, `0x07FE` positive infinity, `0x0802` negative infinity, and `0x0801` reserved. Do not turn them into ordinary floats.

Heart Rate Measurement (`180D/2A37`): parse flags; select 8/16-bit heart rate; conditionally parse energy expended and RR intervals; validate repeated RR field alignment and RFU behavior. Use current Heart Rate Service 1.0 plus mandatory Errata 23224.

Blood Pressure Measurement (`1810/2A35`): parse flags; units bit; three SFLOAT values; optional timestamp, pulse rate, user ID, and measurement status in specified order; preserve unavailable/special values. Use adopted Blood Pressure Service v1.1.1 or the product’s claimed revision. These are protocol values, not medical conclusions.

Name registry labels are hints. Never infer value schema solely from a 16-bit UUID when service context/version disagrees.
