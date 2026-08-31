# AAA examples

## Kotlin result

```kotlin
@Test
fun `expired token is rejected`() {
    val clock = FakeClock(EXPIRED_AT)
    val verifier = TokenVerifier(clock)

    val result = verifier.verify(expiredToken)

    assertEquals(Verification.Expired, result)
}
```

## Exception helper

```kotlin
@Test
fun `negative quantity is rejected`() {
    val cart = Cart()

    val error = assertFailsWith<IllegalArgumentException> {
        cart.add(product, quantity = -1)
    }

    assertEquals("quantity", error.parameterName)
}
```

## Python event

```python
def test_checkout_emits_order_created(bus):
    events = bus.record("order.created")
    checkout = Checkout(bus)

    order = checkout.submit(valid_cart)

    assert events == [OrderCreated(order.id)]
```

## Integration request

```typescript
it("returns conflict for a duplicate idempotency key", async () => {
  const app = await testApp({ existingKey: "k-1" })

  const response = await app.post("/orders", body, { "Idempotency-Key": "k-1" })

  expect(response.status).toBe(409)
  expect(response.body.code).toBe("duplicate_idempotency_key")
})
```

Comments are omitted because whitespace/names make phases clear. Add markers only when a repository convention or complex scenario benefits.
