# libacvp and ACVP file shapes

## Authority order

Use this order when sources disagree:

1. Current NIST ACVP base protocol for common envelope/session semantics.
2. Current exact NIST algorithm specification for registration, prompt, and response fields.
3. Pinned libacvp handler/source for what that release actually accepts and emits.
4. Pinned libacvp fixtures for regression and malformed-input behavior.

The inspected source is `cisco/libacvp@1877259518794f43e4e679f4c5864efa12c32e13`, reporting libacvp 2.3.1 and protocol 1.0. Re-check before changing models.

## ACVP protocol envelope

A common ACVP prompt/response representation is a top-level array:

```json
[
  { "acvVersion": "1.0" },
  {
    "vsId": 123,
    "algorithm": "ACVP-AES-CBC",
    "revision": "1.0",
    "testGroups": []
  }
]
```

Treat the first object as a protocol header only when `acvVersion` is present with the expected JSON type. Do not model the entire array as homogeneous.

The second object can be a vector set, registration/session resource, response, or disposition depending on the endpoint and direction. Classify its required fields before typed decoding.

## Vector hierarchy

The stable hierarchy is:

```text
vector set: vsId, algorithm, [mode], [revision], testGroups[]
  group:    tgId, group discriminators/parameters, tests[]
    case:   tcId, operation-specific input/output fields
```

- `vsId` identifies one vector set across the ACVP instance.
- `tgId` identifies a group within the vector set.
- `tcId` identifies a case throughout the vector set.
- Group fields apply to all child cases unless the algorithm specification says otherwise.
- Request and response shapes share IDs but not necessarily the same fields.

Preserve `testGroups` and `tests` array order. Reject duplicate IDs even if a map conversion would overwrite them.

## libacvp request-only offline bundle

libacvp's request-only writer creates a library-specific top-level array:

```json
[
  {
    "url": "/acvp/v1/testSessions/123",
    "jwt": "<secret>",
    "isSample": false,
    "vectorSetUrls": ["/acvp/v1/testSessions/123/vectorSets/456"]
  },
  {
    "vsId": 456,
    "algorithm": "...",
    "testGroups": []
  }
]
```

The first item is session metadata, not an `acvVersion` header and not a vector set. Remaining items are bare vector-set objects. A response bundle preserves the leading session object and appends response vector sets.

Never print, snapshot, commit, or include the `jwt` value in diagnostics. Treat session files and offline bundles as secret-bearing even when vector data itself is public.

## Session-resume file

A session file is an array containing a session object with fields such as:

- `url`
- `jwt`
- `isSample`
- `vectorSetUrls`
- optional registration/session metadata depending on workflow/version

Do not reuse the vector-set model for this object. Keep credential-bearing session persistence outside ordinary parser fixtures.

## Bare/generic vector set

libacvp's tolerant offline path can accept a bare vector-set object and arrays containing vector sets. Its generic mode supports a single standard vector file from another producer.

A bare object is a vector set only when it has valid `vsId`, `algorithm`, and `testGroups`. A JSON object with `algorithm` alone may instead be a registration capability.

## Registration

Registration JSON describes capabilities, not test execution. It commonly uses the protocol envelope and contains one or more algorithm capability objects with:

- `algorithm`
- optional `mode`
- `revision`
- prerequisite algorithms
- algorithm-specific capability domains/arrays

Registration domains can be arrays of integers or objects such as `{ "min": ..., "max": ..., "increment": ... }`. Model them from the exact algorithm registration schema. Keep registration models separate from prompt groups even when field names match.

## Repository fixtures

Many `test/json/**` fixtures in libacvp use historical `acvVersion` values such as `0.5`; some intentionally exercise malformed or invalid structures. Use each fixture only with the test/source that defines its expectation. Never infer current wire requirements from filename count or one fixture.

## Dispositions and service resources

Server results, request status, vendors, persons, modules, operational environments, and validation resources are base-protocol/service objects, not vector sets. Give each endpoint a separate root type or retain it as `JsonObject` until a named parser exists.
