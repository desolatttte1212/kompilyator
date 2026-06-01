from enum import Enum


class Register(Enum):
    # Integer parameter registers (System V ABI)
    RDI = "rdi"
    RSI = "rsi"
    RDX = "rdx"
    RCX = "rcx"
    R8 = "r8"
    R9 = "r9"

    # Return value register
    RAX = "rax"
    RDX_HI = "rdx"

    # Scratch registers
    R10 = "r10"
    R11 = "r11"

    # Callee-saved registers
    RBX = "rbx"
    RBP = "rbp"
    R12 = "r12"
    R13 = "r13"
    R14 = "r14"
    R15 = "r15"

    # Float / Vector registers
    XMM0 = "xmm0"
    XMM1 = "xmm1"
    XMM2 = "xmm2"
    XMM3 = "xmm3"
    XMM4 = "xmm4"
    XMM5 = "xmm5"
    XMM6 = "xmm6"
    XMM7 = "xmm7"


Registers = Register

INTEGER_PARAM_REGISTERS = [
    Register.RDI, Register.RSI, Register.RDX,
    Register.RCX, Register.R8, Register.R9
]

FLOAT_PARAM_REGISTERS = [
    Register.XMM0, Register.XMM1, Register.XMM2, Register.XMM3,
    Register.XMM4, Register.XMM5, Register.XMM6, Register.XMM7
]