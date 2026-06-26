# RiscvCsrRegfile Python Configuration Parameters

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| mstatus_init | Param.UInt32 | 0x00001800 | Initial value of the mstatus CSR register. Default sets FS=2 (Initial) for floating-point support. |
| priv_init | Param.UInt8 | 3 | Initial privilege level: 0=User, 1=Supervisor, 3=Machine |
| mtvec_base | Param.UInt32 | 0x80000000 | Base address for mtvec (Machine Trap Vector). Lower 2 bits encode the vectoring mode. |
| stvec_base | Param.UInt32 | 0x80000000 | Base address for stvec (Supervisor Trap Vector). Lower 2 bits encode the vectoring mode. |

## Usage Example

```python
from m5.objects import RiscvCsrRegfile

# Create CSR register file with default parameters
csr = RiscvCsrRegfile()

# Or with custom parameters
csr = RiscvCsrRegfile(
    mstatus_init=0x00001800,
    priv_init=3,
    mtvec_base=0x80000000,
    stvec_base=0x80000000
)
```

## Module Type

**Sequential Logic (Submodule)** - This module does not have its own event loop.
It is driven by its parent module (riscv_csr) which calls `process()` every cycle.

## Port Interface

All module I/O is handled via set/get functions (not gem5 ports):

### Input Set Functions
- `setExtIntrI(val)` - External interrupt (bit 0)
- `setTimerIntrI(val)` - Timer interrupt (bit 0)
- `setCpuIdI(val)` - CPU ID for mhartid (32 bits)
- `setMisaI(val)` - MISA register value (32 bits)
- `setExceptionI(val)` - Exception encoding (6 bits: bit5=valid, bit4=interrupt flag, bits3:0=cause)
- `setExceptionPcI(val)` - Exception PC (32 bits)
- `setExceptionAddrI(val)` - Exception address (32 bits)
- `setCsrRenI(val)` - CSR read enable (bit 0)
- `setCsrRaddrI(val)` - CSR read address (12 bits)
- `setCsrWaddrI(val)` - CSR write address (12 bits)
- `setCsrWdataI(val)` - CSR write data (32 bits)

### Output Get Functions
- `getCsrRdataO()` - CSR read data (32 bits)
- `getCsrBranchO()` - CSR branch request (bool)
- `getCsrTargetO()` - CSR branch target address (32 bits)
- `getPrivO()` - Current privilege level (2 bits)
- `getStatusO()` - Status register (mstatus) value (32 bits)
- `getSatpO()` - SATP register value (32 bits)
- `getInterruptO()` - Interrupt pending flags (32 bits, bitmask)
