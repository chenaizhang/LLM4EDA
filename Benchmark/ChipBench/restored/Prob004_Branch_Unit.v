module RefModule #(
  parameter PC_W = 9
) (
  input logic [PC_W-1:0] Cur_PC,
  input logic [31:0] Imm,
  input logic  JalrSel,
  input logic  Branch,
  input logic [31:0] AluResult,
  output logic [31:0] PC_Imm,
  output logic [31:0] PC_Four,
  output logic [31:0] BrPC,
  output logic  PcSel
);
  logic Branch_Sel;
  logic [31:0] PC_Full;

  assign PC_Full = {23'b0, Cur_PC};
  assign PC_Imm = PC_Full + Imm;
  assign PC_Four = PC_Full + 32'b100;
  assign Branch_Sel = Branch && AluResult[0];
  assign BrPC = (JalrSel ? AluResult : (Branch_Sel ? PC_Imm : 32'b0));
  assign PcSel = JalrSel || Branch_Sel;
endmodule
