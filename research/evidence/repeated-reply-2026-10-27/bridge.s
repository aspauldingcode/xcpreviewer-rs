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

.globl _owned_transport_witness
.p2align 2
_owned_transport_witness:
 mov x4,x20
 b _owned_transport_record

.globl _owned_reply_unit
.p2align 2
_owned_reply_unit:
 stp x29,x30,[sp,#-32]!
 mov x29,sp
 stp x20,x21,[sp,#16]
 mov x16,x0
 mov x20,x1
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

.globl _owned_make_handler
.p2align 2
_owned_make_handler:
 stp x29,x30,[sp,#-48]!
 mov x29,sp
 stp x19,x20,[sp,#16]
 str x21,[sp,#32]
 mov x16,x0
 mov x0,x1
 mov x20,x2
 mov x19,x3
 mov x21,xzr
 blr x16
 stp x0,x1,[x19]
 ldr x21,[sp,#32]
 ldp x19,x20,[sp,#16]
 ldp x29,x30,[sp],#48
 ret
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
