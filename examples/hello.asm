section .text
global main

double:
    push rbp
    mov rbp, rsp
    sub rsp, 16  ; Allocate stack space

    ; Block: double_entry
    mov eax, [rbp-24]
    mov [rbp-16], eax
    mov eax, [rbp-16]
    mov [rbp-32], eax  ; load x
    mov eax, [rbp-16]
    mov [rbp-40], eax  ; load x
    mov eax, [rbp-32]
    mov edx, [rbp-40]
    add eax, edx  ; t2 + t3
    mov [rbp-48], eax
    mov eax, [rbp-48]  ; return value
    jmp .double_exit

    .double_exit:
    add rsp, 48  ; Deallocate stack space
    pop rbp
    ret

main:
    push rbp
    mov rbp, rsp
    sub rsp, 16  ; Allocate stack space

    ; Block: main_entry
    mov eax, 0
    mov [rbp-24], eax  ; init i
    mov eax, 3
    mov [rbp-32], eax  ; init limit
    jmp .L_while_header0

    ; Block: L_while_header0
.L_while_header0:
    mov eax, [rbp-24]
    mov [rbp-40], eax  ; load i
    mov eax, [rbp-32]
    mov [rbp-48], eax  ; load limit
    mov eax, [rbp-40]
    mov edx, [rbp-48]
    cmp eax, edx  ; t2 < t3
    setl al
    movzx eax, al
    mov [rbp-56], eax
    mov eax, [rbp-56]
    test eax, eax
    jnz .L_while_body1  ; while condition

    ; Block: L_while_exit2
.L_while_exit2:
    jmp .main_exit

    ; Block: L_while_body1
.L_while_body1:
    mov eax, [rbp-24]
    mov [rbp-64], eax  ; load i
    mov edi, [rbp-64]
    call double  ; call double
    mov [rbp-72], eax
    mov eax, [rbp-72]
    mov [rbp-24], eax  ; store i
    mov eax, [rbp-24]
    mov [rbp-80], eax  ; load i
    mov eax, [rbp-80]
    mov edx, 1
    add eax, edx  ; t7 + 1
    mov [rbp-88], eax
    mov eax, [rbp-88]
    mov [rbp-24], eax  ; store i
    jmp .L_while_header0

    .main_exit:
    add rsp, 96  ; Deallocate stack space
    pop rbp
    ret
