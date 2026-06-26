# RiscvCsr Python Configuration Parameters

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| csrfile | Param.RiscvCsrRegfile | Parent.any | CSR register file submodule |

## Usage Example

```python
from m5.objects import RiscvCsr, RiscvCsrRegfile

# Create CSR register file
csrfile = RiscvCsrRegfile()

# Create CSR module with reference to regfile
csr = RiscvCsr(csrfile=csrfile)
```

## Module Type

**Sequential Logic (Submodule)** - This module does not have its own event loop. It is driven by a parent module which calls `process()` every cycle.

## Port Interface

All module I/O is handled via set/get functions (not gem5 ports):

### Input Set Functions
- `setOpcodeValidI(val)` - Opcode valid flag (bit 0)
- `setOpcodeOpcodeI(val)` - Instruction opcode (32 bits)
- `setOpcodePcI(val)` - Instruction PC (32 bits)
- `setOpcodeInvalidI(val)` - Illegal instruction flag (bit 0)
- `setOpcodeRdIdxI(val)` - Destination register index (5 bits)
- `setOpcodeRaIdxI(val)` - Source operand A register index (5 bits)
- `setOpcodeRbIdxI(val)` - Source operand B register index (5 bits)
- `setOpcodeRaOperandI(val)` - Source operand A value (32 bits)
- `setOpcodeRbOperandI(val)` - Source operand B value (32 bits)
- `setCsrWritebackWriteI(val)` - CSR writeback write enable (bit 0)
- `setCsrWritebackWaddrI(val)` - CSR writeback write address (12 bits)
- `setCsrWritebackWdataI(val)` - CSR writeback write data (32 bits)
- `setCsrWritebackExceptionI(val)` - CSR writeback exception type (6 bits)
- `setCsrWritebackExceptionPcI(val)` - CSR writeback exception PC (32 bits)
- `setCsrWritebackExceptionAddrI(val)` - CSR writeback exception address (32 bits)
- `setCpuIdI(val)` - CPU ID (32 bits)
- `setResetVectorI(val)` - Reset vector base address (32 bits)
- `setIntrI(val)` - External interrupt signal (bit 0)
- `setInterruptInhibitI(val)` - Interrupt inhibit flag (bit 0)

### Output Get Functions
- `getCsrResultE1ValueO()` - CSR result value for E1 stage (32 bits)
- `getCsrResultE1WriteO()` - CSR result write enable for E1 stage (bit 0)
- `getCsrResultE1WdataO()` - CSR result write data for E1 stage (32 bits)
- `getCsrResultE1ExceptionO()` - CSR result exception type for E1 stage (6 bits)
- `getBranchCsrRequestO()` - CSR branch request (bit 0)
- `getBranchCsrPcO()` - CSR branch target PC (32 bits)
- `getBranchCsrPrivO()` - CSR branch target privilege level (2 bits)
- `getTakeInterruptO()` - Interrupt response flag (bit 0)
- `getIfenceO()` - Instruction fence flag (bit 0)
- `getMmuPrivDO()` - MMU data privilege level (2 bits)
- `getMmuSumO()` - MMU SUM flag (bit 0)
- `getMmuMxrO()` - MMU MXR flag (bit 0)
- `getMmuFlushO()` - MMU TLB flush flag (bit 0)
- `getMmuSatpO()` - MMU SATP register value (32 bits)
