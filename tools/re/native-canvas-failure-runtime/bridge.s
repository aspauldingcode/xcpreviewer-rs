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

.globl _owned_swift_scalar
.p2align 2
_owned_swift_scalar:
 stp x29,x30,[sp,#-32]!
 mov x29,sp
 stp x20,x21,[sp,#16]
 mov x16,x0
 mov x0,x1
 mov x1,x2
 mov x2,x3
 mov x3,x4
 mov x20,x5
 mov x21,xzr
 blr x16
 ldp x20,x21,[sp,#16]
 ldp x29,x30,[sp],#32
 ret

.globl _owned_swift_call3
.p2align 2
_owned_swift_call3:
 stp x29,x30,[sp,#-32]!
 mov x29,sp
 stp x20,x21,[sp,#16]
 mov x16,x0
 mov x0,x1
 mov x1,x2
 mov x2,x3
 mov x20,x4
 mov x8,x5
 mov x21,xzr
 blr x16
 mov x0,x21
 ldp x20,x21,[sp,#16]
 ldp x29,x30,[sp],#32
 ret


.globl _owned_handle_init
.p2align 2
_owned_handle_init:
 stp x29,x30,[sp,#-32]!
 mov x29,sp
 stp x20,x21,[sp,#16]
 mov x16,x0
 mov x20,x1
 mov x0,xzr
 mov x1,xzr
 mov x21,xzr
 blr x16
 ldp x20,x21,[sp,#16]
 ldp x29,x30,[sp],#32
 ret
.globl _owned_add_observer
.p2align 2
_owned_add_observer:
 stp x29,x30,[sp,#-32]!
 mov x29,sp
 stp x20,x21,[sp,#16]
 mov x16,x0
 mov x20,x1
 mov x0,x2
 mov x1,x3
 mov x8,x4
 mov x21,xzr
 blr x16
 ldp x20,x21,[sp,#16]
 ldp x29,x30,[sp],#32
 ret
.globl _owned_observer_callback
.p2align 2
_owned_observer_callback:
 mov x1,x0
 mov x0,x20
 b _owned_observer_record
.globl _owned_callsite_init
.p2align 2
_owned_callsite_init:
 stp x29,x30,[sp,#-32]!
 mov x29,sp
 stp x20,x21,[sp,#16]
 mov x16,x0
 mov x8,x1
 mov x20,xzr
 mov x21,xzr
 adrp x0,Lowned_name@PAGE
 add x0,x0,Lowned_name@PAGEOFF
 mov x1,#5
 mov x2,#2
 mov x3,#1
 mov x4,#1
 mov x5,x0
 mov x6,#5
 mov x7,#2
 blr x16
 ldp x20,x21,[sp,#16]
 ldp x29,x30,[sp],#32
 ret
.section __TEXT,__cstring,cstring_literals
Lowned_name:
.asciz "owned"
