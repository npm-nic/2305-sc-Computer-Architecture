"""CPU functionality."""

import sys

HLT = 0b00000001
LDI = 0b10000010
PRN = 0b01000111
MUL = 0b10100010
PUSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
ADD = 0b10100000
RET = 0b00010001
CMP = 0b10100111
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110

SP = 7 # stack pointer starts at 7


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.halted = False
        self.pc = 0 # program counter ... points to the start of the currently-executing instructions
        self.reg[SP] = 0xf4
        self.flags = [0, 0, 0]

        self.branchtable = {}
        self.branchtable[HLT] = self.hlt
        self.branchtable[LDI] = self.ldi
        self.branchtable[PRN] = self.prn
        self.branchtable[CMP] = self.cmp
        self.branchtable[JEQ] = self.jeq
        self.branchtable[ADD] = self.add
        self.branchtable[MUL] = self.mul
        self.branchtable[PUSH] = self.push
        self.branchtable[POP] = self.pop
        self.branchtable[RET] = self.ret
        self.branchtable[CALL] = self.call
        self.branchtable[JMP] = self.jmp
        self.branchtable[JNE] = self.jne

    def load(self):
        """Load a program into memory."""
        address = 0
        if len(sys.argv) != 2:
            print(f"usage: {sys.argv[0]} path/to/filename")
            sys.exit(1)
        try:
            with open(sys.argv[1]) as f:
                for line in f:
                    if len(line.strip().split('#')[0]):
                        self.ram[address] = int(line.strip().split('#')[0], 2)
                        address += 1
        except FileNotFoundError:
            print(f"{sys.argv[0]} >> '{sys.argv[1]}' not found")
            sys.exit(2)

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "CMP":
            if self.reg[reg_a] == self.reg[reg_b]:
                self.flags = [0,0,1]
            if self.reg[reg_a] < self.reg[reg_b]:
                self.flags = [1,0,0]
            if self.reg[reg_a] > self.reg[reg_b]:
                self.flags = [0,1,0]         
            # ⬆️ The register is made up of 8 bits. If a particular bit is set, that flag is "true" ⬇️
            #   FL bits: 00000LGE
            #   -->   L Less-than: during a CMP, set to 1 if registerA is less than registerB, zero otherwise.
            #   -->   G Greater-than: during a CMP, set to 1 if registerA is greater than registerB, zero otherwise.
            #   -->   E Equal: during a CMP, set to 1 if registerA is equal to registerB, zero otherwise.
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def ram_read(self, address):
        return self.ram[address]
    
    def ram_write(self, address, value):
        self.ram[address] = value
        return self.ram[address]

    def hlt(self, operand_a=None, operand_b=None):
        self.halted = True

    def ldi(self, operand_a=None, operand_b=None):
        self.reg[operand_a] = operand_b

    def prn(self, operand_a=None, operand_b=None):
        print(self.reg[operand_a])

    def mul(self, operand_a=None, operand_b=None):
        self.alu("MUL", operand_a, operand_b)

    def push(self, operand_a=None, operand_b=None):
        self.reg[SP] -= 1
        value = self.reg[operand_a]
        self.ram_write(self.reg[SP], value)

    def pop(self, operand_a=None, operand_b=None):
        if self.reg[SP] == 0xF4:
            return 'Empty Stack'
        value = self.ram_read(self.reg[SP])
        self.reg[operand_a] = value
        self.reg[SP] += 1

    def call(self, operand_a=None, operand_b=None):
        return_addr = self.pc + 2
        
        self.reg[SP] -= 1
        top_of_stack_addr = self.reg[SP]
        self.ram_write(self.reg[SP], return_addr)

        reg_num = self.ram[self.pc + 1]
        subroutine_addr = self.reg[reg_num]
        
        self.pc = subroutine_addr

    def add(self, operand_a=None, operand_b=None):
        self.alu("ADD", operand_a, operand_b)

    def ret(self, operand_a=None, operand_b=None):
        value = self.reg[SP]
        return_addr = self.ram[value]
        self.reg[SP] += 1        
        self.pc = self.ram[value]

    def cmp(self, operand_a=None, operand_b=None):
        self.alu("CMP", operand_a, operand_b)

    def jmp(self, operand_a=None, operand_b=None):
        self.pc = self.reg[operand_a]

    def jeq(self, operand_a=None, operand_b=None):
        if self.flags[2]:
            self.pc = self.reg[operand_a]
        else:
            self.pc += 2

    def jne(self, operand_a=None, operand_b=None):
        if not self.flags[2]:
            self.pc = self.reg[operand_a]
        else:
            self.pc += 2

    def run(self):
        """Run the CPU."""
        while not self.halted:
            # capture instruction we are pointing at
            instruction = self.ram_read(self.pc)
            # capture operands for that instruction
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)
            instruction_size = ((instruction & 0b11000000)>>6) + 1
            # ⬆️ find instruction size ... only first 2 digits matter ⬇️
            # --> '& 0b11000000' masks first two values
            # --> '>>' shifts instruction to right '6' places ...
            # --> ex: 0b01000000 >> 6 <==> 0b01 <==> 1 ...argument <==> 2 byte instruction

            if instruction in self.branchtable:
                self.branchtable[instruction](operand_a, operand_b)
            else:
                print(f'unknown instruction: {instruction} at address {self.pc}')
                sys.exit(1)

            if ((instruction >> 4) & 0b1) != 1:
                self.pc += instruction_size