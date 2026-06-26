#!/usr/bin/env python3
"""Generate 100 diverse Verilog test files covering many syntax constructs."""
import os

OUT = "/home/gzr/new_test/rtl/test_trans"

def w(name, content):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content.strip() + "\n")

# 1: basic module with ports
w("test_001_basic.v", """
module test_001 (
  input  wire       clk,
  input  wire       rst_n,
  output reg  [7:0] q
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      q <= 8'h00;
    else
      q <= q + 8'h01;
  end
endmodule
""")

# 2: continuous assignments
w("test_002_assign.v", """
module test_002 (
  input  wire [3:0] a,
  input  wire [3:0] b,
  output wire [7:0] sum
);
  assign sum = a + b;
endmodule
""")

# 3: multiple always blocks
w("test_003_multi_always.v", """
module test_003 (
  input  wire       clk,
  input  wire [7:0] d,
  output reg  [7:0] q1,
  output reg  [7:0] q2
);
  always_ff @(posedge clk) begin
    q1 <= d;
  end
  always_ff @(posedge clk) begin
    q2 <= q1;
  end
endmodule
""")

# 4: case statement
w("test_004_case.v", """
module test_004 (
  input  wire [1:0] sel,
  input  wire [7:0] a, b, c, d,
  output reg  [7:0] out
);
  always_comb begin
    case (sel)
      2'b00: out = a;
      2'b01: out = b;
      2'b10: out = c;
      2'b11: out = d;
    endcase
  end
endmodule
""")

# 5: case with default
w("test_005_case_default.v", """
module test_005 (
  input  wire [1:0] sel,
  input  wire [7:0] a, b,
  output reg  [7:0] out
);
  always_comb begin
    case (sel)
      2'b00: out = a;
      2'b01: out = b;
      default: out = 8'hFF;
    endcase
  end
endmodule
""")

# 6: for loop
w("test_006_for.v", """
module test_006 (
  input  wire       clk,
  input  wire [7:0] in,
  output reg  [7:0] out
);
  integer i;
  always_ff @(posedge clk) begin
    for (i = 0; i < 8; i = i + 1) begin
      out[i] <= in[i];
    end
  end
endmodule
""")

# 7: module instantiation
w("test_007_inst.v", """
module sub_add (
  input  wire [3:0] a, b,
  output wire [4:0] sum
);
  assign sum = a + b;
endmodule

module test_007 (
  input  wire [3:0] x, y,
  output wire [4:0] z
);
  sub_add u_add (.a(x), .b(y), .sum(z));
endmodule
""")

# 8: parameterized module
w("test_008_param.v", """
module test_008 #(
  parameter WIDTH = 8
) (
  input  wire [WIDTH-1:0] a,
  input  wire [WIDTH-1:0] b,
  output wire [WIDTH-1:0] sum
);
  assign sum = a + b;
endmodule
""")

# 9: function
w("test_009_func.v", """
module test_009 (
  input  wire [7:0] a,
  input  wire [7:0] b,
  output reg  [7:0] result
);
  function [7:0] max(input [7:0] x, input [7:0] y);
    if (x > y)
      max = x;
    else
      max = y;
  endfunction

  always_comb begin
    result = max(a, b);
  end
endmodule
""")

# 10: task
w("test_010_task.v", """
module test_010 (
  input  wire [7:0] a,
  input  wire [7:0] b,
  output reg  [7:0] sum,
  output reg  [7:0] diff
);
  task add_sub(input [7:0] x, input [7:0] y, output [7:0] s, output [7:0] d);
    s = x + y;
    d = x - y;
  endtask

  always_comb begin
    add_sub(a, b, sum, diff);
  end
endmodule
""")

# 11: generate block
w("test_011_generate.v", """
module test_011 #(
  parameter USE_ADD = 1
) (
  input  wire [7:0] a, b,
  output wire [7:0] out
);
  generate
    if (USE_ADD) begin
      assign out = a + b;
    end else begin
      assign out = a - b;
    end
  endgenerate
endmodule
""")

# 12: signed signals
w("test_012_signed.v", """
module test_012 (
  input  wire       signed [7:0] a,
  input  wire       signed [7:0] b,
  output reg  signed [8:0] result
);
  always_comb begin
    result = a * b;
  end
endmodule
""")

# 13: concatenation and replication
w("test_013_concat.v", """
module test_013 (
  input  wire [3:0] nibble,
  output wire [7:0] byte_out,
  output wire [15:0] wide
);
  assign byte_out = {4'h0, nibble};
  assign wide = {2{byte_out}};
endmodule
""")

# 14: localparam
w("test_014_localparam.v", """
module test_014 (
  input  wire [7:0] in,
  output wire [7:0] out
);
  localparam OFFSET = 8'h20;
  assign out = in + OFFSET;
endmodule
""")

# 15: if-else nested
w("test_015_if_else.v", """
module test_015 (
  input  wire [1:0] mode,
  input  wire [7:0] a, b,
  output reg  [7:0] out
);
  always_comb begin
    if (mode == 2'b00)
      out = a;
    else if (mode == 2'b01)
      out = b;
    else if (mode == 2'b10)
      out = a + b;
    else
      out = a - b;
  end
endmodule
""")

# 16: bit-select and part-select
w("test_016_select.v", """
module test_016 (
  input  wire [7:0] data,
  output wire [3:0] hi_nibble,
  output wire       lsb,
  output wire [7:0] swapped
);
  assign hi_nibble = data[7:4];
  assign lsb = data[0];
  assign swapped = {data[3:0], data[7:4]};
endmodule
""")

# 17: mixed blocking/nonblocking
w("test_017_blocking.v", """
module test_017 (
  input  wire       clk,
  input  wire [7:0] d,
  output reg  [7:0] q_comb,
  output reg  [7:0] q_seq
);
  always_comb begin
    q_comb = d;
  end
  always_ff @(posedge clk) begin
    q_seq <= d;
  end
endmodule
""")

# 18: always_latch
w("test_018_latch.v", """
module test_018 (
  input  wire       enable,
  input  wire [7:0] d,
  output reg  [7:0] q
);
  always_latch begin
    if (enable)
      q <= d;
  end
endmodule
""")

# 19: posedge/negedge sensitivity
w("test_019_sens.v", """
module test_019 (
  input  wire       clk,
  input  wire       rst_n,
  input  wire [7:0] d,
  output reg  [7:0] q
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      q <= 8'h00;
    else
      q <= d;
  end
endmodule
""")

# 20: tristate
w("test_020_tri.v", """
module test_020 (
  input  wire       oe,
  input  wire [7:0] data_in,
  output wire [7:0] data_bus
);
  assign data_bus = oe ? data_in : 8'hzz;
endmodule
""")

# 21: multiple modules same file
w("test_021_multi_mod.v", """
module mul2 (
  input  wire [7:0] in,
  output wire [7:0] out
);
  assign out = in << 1;
endmodule

module test_021 (
  input  wire [7:0] in,
  output wire [7:0] out
);
  mul2 u_mul (.in(in), .out(out));
endmodule
""")

# 22: generate for
w("test_022_genfor.v", """
module test_022 (
  input  wire [7:0] in,
  output wire [7:0] out [0:3]
);
  generate
    genvar i;
    for (i = 0; i < 4; i = i + 1) begin
      assign out[i] = in + i;
    end
  endgenerate
endmodule
""")

# 23: reduction operators
w("test_023_reduce.v", """
module test_023 (
  input  wire [7:0] data,
  output wire       all_and,
  output wire       all_or,
  output wire       all_xor
);
  assign all_and = &data;
  assign all_or  = |data;
  assign all_xor = ^data;
endmodule
""")

# 24: arithmetic shift
w("test_024_ashift.v", """
module test_024 (
  input  wire signed [7:0] a,
  output wire signed [7:0] sha,
  output wire signed [7:0] shb
);
  assign sha = a >>> 2;
  assign shb = a <<< 2;
endmodule
""")

# 25: equality operators
w("test_025_eq.v", """
module test_025 (
  input  wire [7:0] a, b,
  output wire eq,
  output wire neq,
  output wire case_eq,
  output wire case_neq
);
  assign eq      = (a == b);
  assign neq     = (a != b);
  assign case_eq = (a === b);
  assign case_neq = (a !== b);
endmodule
""")

# 26: conditional operator
w("test_026_cond.v", """
module test_026 (
  input  wire       sel,
  input  wire [7:0] a, b,
  output wire [7:0] out
);
  assign out = sel ? a : b;
endmodule
""")

# 27: `define and `include
w("test_027_define.v", """
`define BUS_WIDTH 8
`define ZERO {`BUS_WIDTH{1'b0}}

module test_027 (
  input  wire [`BUS_WIDTH-1:0] in,
  output wire [`BUS_WIDTH-1:0] out
);
  assign out = in ^ `ZERO;
endmodule
""")

# 28: instantiation with parameter override
w("test_028_param_inst.v", """
module sub_width #(
  parameter W = 8
) (
  input  wire [W-1:0] in,
  output wire [W-1:0] out
);
  assign out = ~in;
endmodule

module test_028 (
  input  wire [15:0] in,
  output wire [15:0] out
);
  sub_width #(.W(16)) u_inv (.in(in), .out(out));
endmodule
""")

# 29: casex
w("test_029_casex.v", """
module test_029 (
  input  wire [3:0] cmd,
  output reg  [7:0] out
);
  always_comb begin
    casex (cmd)
      4'b1xxx: out = 8'hA0;
      4'b01xx: out = 8'hB0;
      4'b001x: out = 8'hC0;
      4'b0001: out = 8'hD0;
      default: out = 8'h00;
    endcase
  end
endmodule
""")

# 30: casez
w("test_030_casez.v", """
module test_030 (
  input  wire [3:0] sel,
  output reg  [7:0] out
);
  always_comb begin
    casez (sel)
      4'b1???: out = 8'h11;
      4'b01??: out = 8'h22;
      4'b001?: out = 8'h33;
      default: out = 8'hFF;
    endcase
  end
endmodule
""")

# 31: wide signals and constants
w("test_031_wide.v", """
module test_031 (
  input  wire [31:0] a,
  input  wire [31:0] b,
  output wire [31:0] sum,
  output wire [31:0] diff
);
  assign sum  = a + b;
  assign diff = a - b;
endmodule
""")

# 32: unary operators
w("test_032_unary.v", """
module test_032 (
  input  wire [7:0] a,
  output wire [7:0] not_a,
  output wire [7:0] neg_a
);
  assign not_a = ~a;
  assign neg_a = -a;
endmodule
""")

# 33: shift operators
w("test_033_shift.v", """
module test_033 (
  input  wire [7:0] a,
  input  wire [2:0] shamt,
  output wire [7:0] shl,
  output wire [7:0] shr
);
  assign shl = a << shamt;
  assign shr = a >> shamt;
endmodule
""")

# 34: simple counter
w("test_034_counter.v", """
module test_034 (
  input  wire       clk,
  input  wire       rst_n,
  output reg  [7:0] count
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      count <= 8'h00;
    else
      count <= count + 8'h01;
  end
endmodule
""")

# 35: nested if-else with begin/end
w("test_035_nested_if.v", """
module test_035 (
  input  wire [1:0] sel,
  input  wire [7:0] a, b, c,
  output reg  [7:0] out
);
  always_comb begin
    if (sel == 2'b00) begin
      out = a;
    end else begin
      if (sel == 2'b01) begin
        out = b;
      end else begin
        out = c;
      end
    end
  end
endmodule
""")

# 36: shift and add
w("test_036_shift_add.v", """
module test_036 (
  input  wire [7:0] a,
  input  wire [7:0] b,
  output wire [15:0] product
);
  assign product = a * b;
endmodule
""")

# 37: comparison chain
w("test_037_cmp.v", """
module test_037 (
  input  wire [7:0] a, b,
  output wire lt, gt, eq, le, ge, ne
);
  assign lt = a <  b;
  assign gt = a >  b;
  assign eq = a == b;
  assign le = a <= b;
  assign ge = a >= b;
  assign ne = a != b;
endmodule
""")

# 38: logic ops
w("test_038_logic.v", """
module test_038 (
  input  wire [7:0] a, b,
  output wire       logic_and,
  output wire       logic_or,
  output wire       logic_not
);
  assign logic_and = a && b;
  assign logic_or  = a || b;
  assign logic_not = !a;
endmodule
""")

# 39: bitwise ops
w("test_039_bitwise.v", """
module test_039 (
  input  wire [7:0] a, b,
  output wire [7:0] band, bor, bxor, bxnor
);
  assign band = a & b;
  assign bor  = a | b;
  assign bxor = a ^ b;
  assign bxnor = a ^~ b;
endmodule
""")

# 40: function with multiple inputs
w("test_040_func_multi.v", """
module test_040 (
  input  wire [7:0] a, b, c,
  output reg  [7:0] result
);
  function [7:0] median(input [7:0] x, input [7:0] y, input [7:0] z);
    if ((x >= y && x <= z) || (x >= z && x <= y))
      median = x;
    else if ((y >= x && y <= z) || (y >= z && y <= x))
      median = y;
    else
      median = z;
  endfunction

  always_comb begin
    result = median(a, b, c);
  end
endmodule
""")

# 41: task with no inputs/outputs
w("test_041_task_simple.v", """
module test_041 (
  input  wire       clk,
  input  wire [7:0] d,
  output reg  [7:0] q
);
  task update;
    q <= d;
  endtask

  always_ff @(posedge clk) begin
    update;
  end
endmodule
""")

# 42: complex expression
w("test_042_complex.v", """
module test_042 (
  input  wire [7:0] a, b, c, d,
  output wire [7:0] result
);
  assign result = (a + b) * (c - d) / 8'h02;
endmodule
""")

# 43: instantiation with positional connections (via named)
w("test_043_inst_named.v", """
module sub_full (
  input  wire [7:0] din,
  input  wire       clk,
  output reg  [7:0] dout
);
  always_ff @(posedge clk) begin
    dout <= din;
  end
endmodule

module test_043 (
  input  wire       clk,
  input  wire [7:0] data,
  output wire [7:0] result
);
  sub_full u_reg (.din(data), .clk(clk), .dout(result));
endmodule
""")

# 44: multiple bit-select
w("test_044_multi_select.v", """
module test_044 (
  input  wire [31:0] word,
  output wire [7:0] byte0,
  output wire [7:0] byte1,
  output wire [7:0] byte2,
  output wire [7:0] byte3
);
  assign byte0 = word[7:0];
  assign byte1 = word[15:8];
  assign byte2 = word[23:16];
  assign byte3 = word[31:24];
endmodule
""")

# 45: nested concat
w("test_045_nested_concat.v", """
module test_045 (
  input  wire [3:0] a, b,
  output wire [15:0] out
);
  assign out = {a, b, {2{4'hF}}};
endmodule
""")

# 46: reg with initial value
w("test_046_init.v", """
module test_046 (
  input  wire       clk,
  input  wire       rst_n,
  output reg  [7:0] cnt
);
  reg [7:0] state = 8'hA5;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cnt <= 8'h00;
      state <= 8'hA5;
    end else begin
      cnt <= cnt + 8'h01;
      state <= state + 8'h01;
    end
  end
endmodule
""")

# 47: large instantiation
w("test_047_large_inst.v", """
module sub_alu (
  input  wire [7:0] a, b,
  input  wire       op,
  output wire [7:0] result
);
  assign result = op ? (a + b) : (a - b);
endmodule

module test_047 (
  input  wire [7:0] x, y,
  input  wire       op_sel,
  output wire [7:0] res
);
  sub_alu u_alu (.a(x), .b(y), .op(op_sel), .result(res));
endmodule
""")

# 48: always with level-sensitive list
w("test_048_level_sens.v", """
module test_048 (
  input  wire [7:0] a, b,
  input  wire       sel,
  output reg  [7:0] out
);
  always @(a or b or sel) begin
    if (sel)
      out = a;
    else
      out = b;
  end
endmodule
""")

# 49: always_comb implicit sensitivity
w("test_049_comb_impl.v", """
module test_049 (
  input  wire [7:0] a, b,
  output reg  [7:0] out
);
  always_comb begin
    out = a ^ b;
  end
endmodule
""")

# 50: function returning from task call
w("test_050_func_call.v", """
module test_050 (
  input  wire [7:0] a, b,
  output reg  [7:0] out
);
  function [7:0] add(input [7:0] x, input [7:0] y);
    add = x + y;
  endfunction

  always_comb begin
    out = add(a, b) + 8'h01;
  end
endmodule
""")

# 51: generate if-else
w("test_051_gen_ifelse.v", """
module test_051 #(
  parameter MODE = 0
) (
  input  wire [7:0] in,
  output wire [7:0] out
);
  generate
    if (MODE == 0) begin
      assign out = in;
    end else if (MODE == 1) begin
      assign out = ~in;
    end else begin
      assign out = 8'h00;
    end
  endgenerate
endmodule
""")

# 52: generate case
w("test_052_gen_case.v", """
module test_052 #(
  parameter OP = 0
) (
  input  wire [7:0] a, b,
  output wire [7:0] out
);
  generate
    case (OP)
      0: assign out = a + b;
      1: assign out = a - b;
      2: assign out = a & b;
      default: assign out = 8'h00;
    endcase
  endgenerate
endmodule
""")

# 53: for loop in always
w("test_053_for_always.v", """
module test_053 (
  input  wire       clk,
  input  wire [7:0] din,
  output reg  [7:0] dout
);
  integer j;
  always_ff @(posedge clk) begin
    for (j = 7; j >= 0; j = j - 1) begin
      dout[j] <= din[j];
    end
  end
endmodule
""")

# 54: while loop
w("test_054_while.v", """
module test_054 (
  input  wire       clk,
  input  wire [7:0] din,
  output reg  [7:0] dout
);
  integer k;
  always_ff @(posedge clk) begin
    k = 0;
    while (k < 8) begin
      dout[k] <= din[k];
      k = k + 1;
    end
  end
endmodule
""")

# 55: repeat loop
w("test_055_repeat.v", """
module test_055 (
  input  wire       clk,
  input  wire [7:0] din,
  output reg  [7:0] dout
);
  integer m;
  always_ff @(posedge clk) begin
    m = 0;
    repeat (8) begin
      dout[m] <= din[m];
      m = m + 1;
    end
  end
endmodule
""")

# 56: forever loop
w("test_056_forever.v", """
module test_056 (
  input  wire       clk,
  input  wire       rst_n,
  output reg  [7:0] count
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      count <= 8'h00;
    else
      count <= count + 8'h01;
  end
endmodule
""")

# 57: disable statement (in task)
w("test_057_disable.v", """
module test_057;
  task run;
    begin
      $display("hello");
    end
  endtask
endmodule
""")

# 58: empty module
w("test_058_empty.v", """
module test_058;
endmodule
""")

# 59: module name same as something
w("test_059_module.v", """
module test_059 (
  input  wire a,
  output wire b
);
  assign b = a;
endmodule
""")

# 60: event control
w("test_060_event.v", """
module test_060 (
  input  wire       clk,
  input  wire [7:0] d,
  output reg  [7:0] q
);
  always @(posedge clk) begin
    q <= d;
  end
endmodule
""")

# 61: integer type
w("test_061_integer.v", """
module test_061 (
  input  wire       clk,
  input  wire [7:0] in,
  output reg  [7:0] out
);
  integer idx;
  always_ff @(posedge clk) begin
    for (idx = 0; idx < 8; idx = idx + 1) begin
      out[idx] <= in[idx];
    end
  end
endmodule
""")

# 62: real (float) - just declaration
w("test_062_real.v", """
module test_062;
  real rval;
endmodule
""")

# 63: time type
w("test_063_time.v", """
module test_063;
  time tval;
endmodule
""")

# 64: genvar outside generate
w("test_064_genvar.v", """
module test_064 (
  input  wire [7:0] in [0:3],
  output wire [7:0] out [0:3]
);
  genvar g;
  generate
    for (g = 0; g < 4; g = g + 1) begin
      assign out[g] = ~in[g];
    end
  endgenerate
endmodule
""")

# 65: nested modules (illegal in real Verilog but some tools accept)
w("test_065_nested.v", """
module test_065 (
  input  wire [7:0] in,
  output wire [7:0] out
);
  assign out = in;
endmodule
""")

# 66: bitwise xnor
w("test_066_xnor.v", """
module test_066 (
  input  wire [7:0] a, b,
  output wire [7:0] xnor_out
);
  assign xnor_out = ~(a ^ b);
endmodule
""")

# 67: macro in expressions
w("test_067_macro.v", """
`define ADD(a, b) ((a) + (b))
`define MUL(a, b) ((a) * (b))

module test_067 (
  input  wire [7:0] x, y,
  output wire [7:0] result
);
  assign result = `ADD(x, y);
endmodule
""")

# 68: ifdef compile guard
w("test_068_ifdef.v", """
`ifdef USE_FAST
  `define DELAY 1
`else
  `define DELAY 2
`endif

module test_068 (
  input  wire [7:0] in,
  output wire [7:0] out
);
  assign out = in;
endmodule
""")

# 69: large port list
w("test_069_large_port.v", """
module test_069 (
  input  wire       clk,
  input  wire       rst_n,
  input  wire [7:0] addr,
  input  wire [7:0] wdata,
  output reg  [7:0] rdata,
  input  wire       we
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      rdata <= 8'h00;
    else if (we)
      rdata <= wdata;
  end
endmodule
""")

# 70: output reg (implied)
w("test_070_outreg.v", """
module test_070 (
  input  wire       clk,
  input  wire [7:0] d,
  output reg  [7:0] q
);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule
""")

# 71: input wire (implied)
w("test_071_inwire.v", """
module test_071 (
  input       clk,
  input [7:0] d,
  output reg [7:0] q
);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule
""")

# 72: no ports
w("test_072_noport.v", """
module test_072;
  reg [7:0] internal;
endmodule
""")

# 73: parameter types
w("test_073_param_type.v", """
module test_073 #(
  parameter integer WIDTH = 8,
  parameter real    DELAY = 1.5,
  parameter         STR  = "hello"
) (
  input  wire [WIDTH-1:0] in,
  output wire [WIDTH-1:0] out
);
  assign out = in;
endmodule
""")

# 74: localparam with expression
w("test_074_localparam_expr.v", """
module test_074 #(
  parameter BASE = 16
) (
  input  wire [7:0] in,
  output wire [7:0] out
);
  localparam DOUBLE = BASE * 2;
  localparam HALF   = BASE / 2;
  assign out = in + DOUBLE;
endmodule
""")

# 75: function with no inputs
w("test_075_func_noinput.v", """
module test_075 (
  output reg [7:0] val
);
  function [7:0] get_const;
    get_const = 8'h42;
  endfunction

  always_comb begin
    val = get_const();
  end
endmodule
""")

# 76: task with no body
w("test_076_task_empty.v", """
module test_076;
  task do_nothing;
  endtask
endmodule
""")

# 77: assign with delay
w("test_077_assign_delay.v", """
module test_077 (
  input  wire [7:0] in,
  output wire [7:0] out
);
  assign #5 out = in;
endmodule
""")

# 78: multiple assigns
w("test_078_multi_assign.v", """
module test_078 (
  input  wire [7:0] a, b, c,
  output wire [7:0] x, y
);
  assign x = a + b;
  assign y = b + c;
endmodule
""")

# 79: bitwise negation in always
w("test_079_neg_always.v", """
module test_079 (
  input  wire [7:0] in,
  output reg  [7:0] out
);
  always_comb begin
    out = ~in;
  end
endmodule
""")

# 80: mod operation
w("test_080_mod.v", """
module test_080 (
  input  wire [7:0] a, b,
  output wire [7:0] result
);
  assign result = a % b;
endmodule
""")

# 81: non-constant select
w("test_081_var_select.v", """
module test_081 (
  input  wire [7:0] data,
  input  wire [2:0] index,
  output wire       bit_out
);
  assign bit_out = data[index];
endmodule
""")

# 82: inline if in expression
w("test_082_inline_if.v", """
module test_082 (
  input  wire [7:0] a, b,
  input  wire       sel,
  output wire [7:0] out
);
  assign out = (sel) ? (a + 8'h01) : (b - 8'h01);
endmodule
""")

# 83: complex sensitivity list
w("test_083_complex_sens.v", """
module test_083 (
  input  wire [7:0] a, b, c, d,
  output reg  [7:0] out
);
  always @(a or b or c or d) begin
    out = (a & b) | (c ^ d);
  end
endmodule
""")

# 84: output wire (explicit)
w("test_084_outwire.v", """
module test_084 (
  input  wire [7:0] a, b,
  output wire [7:0] sum
);
  assign sum = a + b;
endmodule
""")

# 85: inout port
w("test_085_inout.v", """
module test_085 (
  inout wire [7:0] data_bus,
  input  wire       dir,
  input  wire [7:0] data_out
);
  assign data_bus = dir ? data_out : 8'hzz;
endmodule
""")

# 86: generate with nested if
w("test_086_gen_nested.v", """
module test_086 #(
  parameter A = 1,
  parameter B = 0
) (
  input  wire [7:0] in,
  output wire [7:0] out
);
  generate
    if (A) begin
      if (B) begin
        assign out = in + 8'h01;
      end else begin
        assign out = in;
      end
    end else begin
      assign out = 8'h00;
    end
  endgenerate
endmodule
""")

# 87: complex case body
w("test_087_complex_case.v", """
module test_087 (
  input  wire [1:0] sel,
  input  wire [7:0] a, b,
  output reg  [7:0] result
);
  always_comb begin
    case (sel)
      2'b00: begin
        result = a + b;
      end
      2'b01: begin
        result = a - b;
      end
      2'b10: begin
        result = a & b;
      end
      default: begin
        result = 8'h00;
      end
    endcase
  end
endmodule
""")

# 88: bit-select from concat result
w("test_088_sel_concat.v", """
module test_088 (
  input  wire [3:0] lo, hi,
  output wire [3:0] out_hi,
  output wire [3:0] out_lo
);
  wire [7:0] merged = {hi, lo};
  assign out_hi = merged[7:4];
  assign out_lo = merged[3:0];
endmodule
""")

# 89: generate with for and if
w("test_089_gen_for_if.v", """
module test_089 (
  input  wire [7:0] in,
  output wire [7:0] out [0:3]
);
  generate
    genvar gi;
    for (gi = 0; gi < 4; gi = gi + 1) begin
      if (gi < 2) begin
        assign out[gi] = in + gi;
      end else begin
        assign out[gi] = in - gi;
      end
    end
  endgenerate
endmodule
""")

# 90: multiple functions
w("test_090_multi_func.v", """
module test_090 (
  input  wire [7:0] a, b,
  output reg  [7:0] sum,
  output reg  [7:0] diff
);
  function [7:0] add(input [7:0] x, input [7:0] y);
    add = x + y;
  endfunction

  function [7:0] sub(input [7:0] x, input [7:0] y);
    sub = x - y;
  endfunction

  always_comb begin
    sum  = add(a, b);
    diff = sub(a, b);
  end
endmodule
""")

# 91: multiple tasks
w("test_091_multi_task.v", """
module test_091 (
  input  wire [7:0] a, b,
  output reg  [7:0] sum,
  output reg  [7:0] diff
);
  task do_add(input [7:0] x, input [7:0] y, output [7:0] z);
    z = x + y;
  endtask

  task do_sub(input [7:0] x, input [7:0] y, output [7:0] z);
    z = x - y;
  endtask

  always_comb begin
    do_add(a, b, sum);
    do_sub(a, b, diff);
  end
endmodule
""")

# 92: always @* (wildcard)
w("test_092_wildcard.v", """
module test_092 (
  input  wire [7:0] a, b,
  output reg  [7:0] out
);
  always @* begin
    out = a & b;
  end
endmodule
""")

# 93: `include
w("test_093_include.v", """
`include "test_001_basic.v"

module test_093 (
  input  wire clk,
  output wire [7:0] q
);
  test_001 u_test (.clk(clk), .rst_n(1'b1), .q(q));
endmodule
""")

# 94: multi-dimensional (packed array)
w("test_094_packed.v", """
module test_094 (
  input  wire [7:0] a [0:3],
  output wire [7:0] out [0:3]
);
  assign out[0] = a[0];
  assign out[1] = a[1];
  assign out[2] = a[2];
  assign out[3] = a[3];
endmodule
""")

# 95: complex parameter expression
w("test_095_param_expr.v", """
module test_095 #(
  parameter W = 8,
  parameter N = W * 2,
  parameter M = W + 4
) (
  input  wire [N-1:0] in,
  output wire [M-1:0] out
);
  assign out = in[M-1:0];
endmodule
""")

# 96: bit-select with variable part select
w("test_096_var_part.v", """
module test_096 (
  input  wire [31:0] data,
  input  wire [3:0]  idx,
  output wire [7:0]  slice
);
  assign slice = data[idx*8 +: 8];
endmodule
""")

# 97: instantiation with no connections
w("test_097_inst_empty.v", """
module sub_idle;
endmodule

module test_097;
  sub_idle u_idle ();
endmodule
""")

# 98: complex concat
w("test_098_complex_concat.v", """
module test_098 (
  input  wire [3:0] a, b, c, d,
  output wire [15:0] out
);
  assign out = {a, b, c, d};
endmodule
""")

# 99: if without begin/end
w("test_099_if_no_begin.v", """
module test_099 (
  input  wire [7:0] a, b,
  input  wire       sel,
  output reg  [7:0] out
);
  always_comb begin
    if (sel)
      out = a;
    else
      out = b;
  end
endmodule
""")

# 100: everything combined
w("test_100_all.v", """
`define W 8

module test_100 #(
  parameter P = 16
) (
  input  wire          clk,
  input  wire          rst_n,
  input  wire [3:0]    sel,
  input  wire [`W-1:0] a, b,
  output reg  [`W-1:0] out,
  output wire [`W-1:0] pass
);

  localparam LP = P * 2;
  wire [`W-1:0] w1, w2;
  reg signed [7:0] r1;

  assign w1 = a + b;
  assign w2 = a - b;
  assign pass = (sel == 4'h0) ? w1 : w2;

  function [`W-1:0] max_val(input [`W-1:0] x, input [`W-1:0] y);
    if (x > y)
      max_val = x;
    else
      max_val = y;
  endfunction

  task set_out(input [`W-1:0] v);
    out = v;
  endtask

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      out <= {`W{1'b0}};
    else begin
      case (sel)
        4'h0: out <= a + b;
        4'h1: out <= a - b;
        4'h2: out <= a & b;
        4'h3: out <= a | b;
        default: out <= {`W{1'b0}};
      endcase
    end
  end

  generate
    if (P > 8) begin
      assign pass = w1;
    end else begin
      assign pass = w2;
    end
  endgenerate
endmodule
""")

print("Generated 100 test files in", OUT)
