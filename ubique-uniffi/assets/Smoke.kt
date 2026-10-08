package example.smoke

import example.ubique.ArithmeticException
import example.ubique.Greeter
import example.ubique.checkedAdd

fun main() {
    check(checkedAdd(2, 3) == 5)
    check(checkedAdd(Int.MIN_VALUE, 0) == Int.MIN_VALUE)
    try {
        checkedAdd(Int.MAX_VALUE, 1)
        error("overflow did not cross the FFI as a typed exception")
    } catch (_: ArithmeticException) {
        println("typed overflow: observed")
    }
    val greeter = Greeter("Grüezi")
    try {
        check(greeter.greet("Kotlin") == "Grüezi, Kotlin!")
    } finally {
        greeter.close()
    }
    val postCloseRejected = try {
        greeter.greet("closed")
        false
    } catch (_: IllegalStateException) {
        true
    }
    check(postCloseRejected) { "closed object remained callable" }
    println("post-close call: rejected")
    greeter.close()
    println("Ubique Rust/Kotlin: result, boundary, typed error, Unicode buffer and object lifecycle passed")
}
