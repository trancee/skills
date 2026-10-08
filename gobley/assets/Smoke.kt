package example.smoke

import example.gobley.ArithmeticException
import example.gobley.Greeter
import example.gobley.checkedAdd

fun main() {
    check(checkedAdd(2, 3) == 5)
    check(checkedAdd(Int.MIN_VALUE, 0) == Int.MIN_VALUE)
    try {
        checkedAdd(Int.MAX_VALUE, 1)
        error("overflow did not cross the FFI as a typed exception")
    } catch (_: ArithmeticException) {
        println("typed overflow: observed")
    }
    val greeter = Greeter("Hello")
    try {
        check(greeter.greet("Rust 🦀") == "Hello, Rust 🦀!")
    } finally {
        greeter.close()
    }
    println("Rust/Kotlin Gobley calls: checked addition, boundary, typed error, Unicode object call and close passed")
}
