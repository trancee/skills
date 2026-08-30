# Kotlin export mappings

Source: [Swift/Objective-C interoperability](https://kotlinlang.org/docs/native-objc-interop.html).

## API controls

- `@ObjCName`: stable Swift/Objective-C class/declaration/parameter name
- `@HiddenFromObjC`: omit declaration from Objective-C/Swift while retaining Kotlin visibility
- `@ShouldRefineInSwift`: export as `swift_private`/`__name` for a Swift wrapper
- `@Throws`: listed Kotlin exceptions become NSError/Swift throws
- `@OverrideInit`: override imported Objective-C initializer
- `@ObjCSignatureOverride`: disambiguate inherited selector methods with clashing Kotlin signatures

Generated header/interface is authoritative.

## Shape mappings

- class -> Objective-C interface / Swift class
- interface -> protocol
- object/companion -> `shared`/`companion`
- top-level declarations -> generated `<File>Kt` class
- enum -> class with static values; Swift switch requires default
- String/collections -> Objective-C bridge then Swift copy; use NSString/NSArray/NSDictionary/NSSet when avoiding conversion is measured and acceptable
- nullable primitives -> boxed KotlinNumber subclasses
- function type -> block/closure; primitive params boxed and Unit return may require KotlinUnit
- inline/value class -> not properly supported in headers

Objective-C lacks packages. Same simple class names can be compiler-renamed by an unstable algorithm; give APIs unique names.

## Generics

Objective-C lightweight generics support only class generics, not function/protocol generics. Kotlin constraints/variance lose information. Unbounded `T` returns appear nullable; `T : Any` preserves non-null header semantics. `-Xno-objc-generics` disables header generics only with deliberate API review.

## Suspend/errors

Suspend exports completion handlers and can appear as Swift async since Swift 5.5, but compiler-native async export remains highly experimental. Completion may run off Main. Suspend without `@Throws` propagates only cancellation; non-suspend without `@Throws` propagates no Kotlin exception and escaping exceptions terminate.
