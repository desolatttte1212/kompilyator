
MiniCompiler Runtime Library (Linux x86-64 System V ABI)
Для запуска требует Linux (или WSL).


section .text


 print_int(rdi): Печатает целое число из регистра RDI

global print_int
print_int:
    push rbp
    mov rbp, rsp
    sub rsp, 40              ; Буфер для строки

    ; Сохраняем исходное число
    mov rbx, rdi

    ; Если число 0, печатаем "0"
    test rbx, rbx
    jnz .convert
    mov byte [rsp], '0'
    mov rcx, 1
    jmp .print

.convert:
    ; Обработка отрицательных чисел
    test rbx, rbx
    jns .positive
    neg rbx
    mov byte [rsp], '-'
    mov rcx, 1
    jmp .loop

.positive:
    mov rcx, 0

.loop:
    ; Делим на 10
    mov rax, rbx
    mov rdx, 0
    mov rbx, 10
    div rbx
    ; rbx теперь 10, остаток в rdx
    add dl, '0'
    mov [rsp + rcx], dl
    inc rcx
    test rax, rax
    jnz .loop

    ; Теперь строка в стеке задом наперед, переворачиваем
    mov r8, 0
    mov r9, rcx
    dec r9

.reverse:
    cmp r8, r9
    jge .print
    mov al, [rsp + r8]
    mov bl, [rsp + r9]
    mov [rsp + r8], bl
    mov [rsp + r9], al
    inc r8
    dec r9
    jmp .reverse

.print:
    ; Syscall: sys_write
    mov rax, 1               ; 1 = sys_write
    mov rdi, 1               ; 1 = stdout
    mov rsi, rsp             ; buffer
    mov rdx, rcx             ; length
    syscall

    add rsp, 40
    pop rbp
    ret


 exit(rdi): Завершает программу с кодом возврата из RDI

global exit
exit:
    mov rax, 60              ; 60 = sys_exit
    syscall
    ; Не возвращается