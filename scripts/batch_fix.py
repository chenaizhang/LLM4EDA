#!/usr/bin/env python3
"""Batch fix remaining compilation errors in custom/riscv.

1. Add #include "custom/riscv/riscv_defines.hh" to files missing it
2. For specific files, handle particular issues
"""

import re
import os
import subprocess

SRC = "/home/gzr/new_test/gem5/src/custom/riscv"

def ensure_defines_include(cc_file):
    """Add the defines header include if missing."""
    path = os.path.join(SRC, cc_file)
    with open(path) as f:
        content = f.read()
    
    if '#include "custom/riscv/riscv_defines.hh"' in content:
        return False
    
    # Add after the first local include (the module's own header)
    content = content.replace(
        f'#include "custom/riscv/{cc_file.replace(".cc", ".hh")}"',
        f'#include "custom/riscv/{cc_file.replace(".cc", ".hh")}"\n#include "custom/riscv/riscv_defines.hh"'
    )
    with open(path, 'w') as f:
        f.write(content)
    return True


def add_decode_instruction(cc_file):
    """Add decodeInstruction function to riscv_decode.cc."""
    path = os.path.join(SRC, cc_file)
    with open(path) as f:
        content = f.read()
    
    if 'void decodeInstruction' in content:
        return False
    
    # Add a simple decode function before evaluate()
    decode_func = """
void
RiscvDecode::decodeInstruction(uint32_t opcode, uint32_t &alu_op, uint32_t &imm, uint32_t &rd, 
                               uint32_t &rs1, uint32_t &rs2, uint32_t &funct3, uint32_t &funct7)
{
    // RISC-V instruction decode
    uint32_t opcode_bits = opcode & 0x7f;
    rd = (opcode >> 7) & 0x1f;
    funct3 = (opcode >> 12) & 0x7;
    rs1 = (opcode >> 15) & 0x1f;
    rs2 = (opcode >> 20) & 0x1f;
    funct7 = (opcode >> 25) & 0x7f;
    alu_op = opcode;
    imm = 0;
    
    // I-immediate: [31:20]
    uint32_t imm_i = (opcode >> 20) & 0xFFF;
    if (opcode & 0x80000000) imm_i |= 0xFFFFF000;
    
    // S-immediate: [31:25][11:7]
    uint32_t imm_s = ((opcode >> 25) & 0x7F) << 5;
    imm_s |= (opcode >> 7) & 0x1F;
    if (opcode & 0x80000000) imm_s |= 0xFFFFF000;
    
    // B-immediate
    uint32_t imm_b = ((opcode >> 31) & 0x1) << 12;
    imm_b |= ((opcode >> 7) & 0x1) << 11;
    imm_b |= ((opcode >> 25) & 0x3F) << 5;
    imm_b |= ((opcode >> 8) & 0xF) << 1;
    if (opcode & 0x80000000) imm_b |= 0xFFFFF000;
    
    // U-immediate: [31:12]
    uint32_t imm_u = opcode & 0xFFFFF000;
    
    // J-immediate
    uint32_t imm_j = ((opcode >> 31) & 0x1) << 20;
    imm_j |= ((opcode >> 12) & 0xFF) << 12;
    imm_j |= ((opcode >> 20) & 0x1) << 11;
    imm_j |= ((opcode >> 21) & 0x3FF) << 1;
    if (opcode & 0x80000000) imm_j |= 0xFFF00000;
    
    switch (opcode_bits) {
        case 0x13: // OP-IMM
            imm = imm_i;
            break;
        case 0x33: // OP
            imm = 0;
            break;
        case 0x03: // LOAD
            imm = imm_i;
            break;
        case 0x23: // STORE
            imm = imm_s;
            break;
        case 0x63: // BRANCH
            imm = imm_b;
            break;
        case 0x37: // LUI
            imm = imm_u;
            break;
        case 0x17: // AUIPC
            imm = imm_u;
            break;
        case 0x6f: // JAL
            imm = imm_j;
            break;
        case 0x67: // JALR
            imm = imm_i;
            break;
        default:
            imm = imm_i;
            break;
    }
}
"""
    
    # Insert decodeInstruction before evaluate()
    eval_pos = content.find('\nvoid\nRiscvDecode::evaluate')
    if eval_pos == -1:
        eval_pos = content.find('void RiscvDecode::evaluate')
    
    if eval_pos >= 0:
        content = content[:eval_pos] + '\n' + decode_func + '\n' + content[eval_pos:]
    else:
        # Add before namespace closing
        content = content.replace('} // namespace gem5', decode_func + '\n} // namespace gem5')
    
    with open(path, 'w') as f:
        f.write(content)
    return True


def add_buffer_q_members(hh_file):
    """Add buffer_q_high, buffer_q_low as member variables."""
    path = os.path.join(SRC, hh_file)
    with open(path) as f:
        content = f.read()
    
    changed = False
    if 'buffer_q_high' not in content:
        content = content.replace('  private:', '  private:\n    uint64_t buffer_q_high = 0;\n    uint64_t buffer_q_low = 0;')
        changed = True
    
    if changed:
        with open(path, 'w') as f:
            f.write(content)
    return changed


def add_helper_funcs():
    """Add missing helper functions and member variables."""
    
    # riscv_decode.hh: add decodeInstruction declaration
    dh_path = os.path.join(SRC, "riscv_decode.hh")
    with open(dh_path) as f:
        content = f.read()
    
    if 'void decodeInstruction' not in content:
        content = content.replace(
            '    void evaluate();',
            '    void decodeInstruction(uint32_t opcode, uint32_t &alu_op, uint32_t &imm, \n'
            '                          uint32_t &rd, uint32_t &rs1, uint32_t &rs2, \n'
            '                          uint32_t &funct3, uint32_t &funct7);\n'
            '    void evaluate();'
        )
        with open(dh_path, 'w') as f:
            f.write(content)
        print("Added decodeInstruction to riscv_decode.hh")


def add_riscv_csr_functions():
    """Fix riscv_csr.cc missing wire names."""
    path = os.path.join(SRC, "riscv_csr.cc")
    with open(path) as f:
        content = f.read()
    
    # These _w vars should be local variables in evaluate
    # Find evaluate() start
    eval_match = re.search(r'void\s+\w+::evaluate\s*\(\s*\)\s*\n?\{', content)
    if not eval_match:
        return False
    
    brace_pos = eval_match.end() - 1
    line_end = content.index('\n', brace_pos)
    insert_pos = line_end + 1
    
    # Add declarations for known _w vars used in riscv_csr.cc
    decls = """    uint32_t csr_addr = 0;
    uint32_t csr_wdata = 0;
    uint32_t csr_write = 0;
    uint32_t csr_status = 0;
    uint32_t satp_reg_w = 0;
    uint32_t status_reg_w = 0;
    uint32_t csr_fault_w = 0;
"""
    
    content = content[:insert_pos] + '\n' + decls + content[insert_pos:]
    with open(path, 'w') as f:
        f.write(content)
    return True


def main():
    add_helper_funcs()
    
    cc_files = sorted([f for f in os.listdir(SRC) if f.endswith('.cc')])
    
    for cc_file in cc_files:
        path = os.path.join(SRC, cc_file)
        
        # Ensure defines header is included
        if ensure_defines_include(cc_file):
            print(f"{cc_file}: added defines header include")
        
        # Special handling for specific files
        base = cc_file.replace('.cc', '')
        
        if base == 'riscv_decode':
            add_buffer_q_members(f'{base}.hh')
            add_decode_instruction(cc_file)
        elif base == 'riscv_csr':
            add_riscv_csr_functions()

if __name__ == '__main__':
    main()
