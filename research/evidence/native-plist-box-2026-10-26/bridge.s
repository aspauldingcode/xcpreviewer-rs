.text
.p2align 2
.globl _owned_swift_call
_owned_swift_call:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x20, x21, [sp, #16]
    mov x16, x0
    mov x0, x1
    mov x1, x2
    mov x20, x3
    mov x8, x4
    mov x21, xzr
    blr x16
    mov x0, x21
    ldp x20, x21, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
