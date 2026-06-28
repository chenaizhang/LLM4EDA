module RefModule (
  input logic [6:0] Opcode,
  output logic  ALUSrc,
  output logic  MemtoReg,
  output logic  RegWrite,
  output logic  MemRead,
  output logic  MemWrite,
  output logic [1:0] ALUOp,
  output logic  Branch,
  output logic  JalrSel,
  output logic [1:0] RWSel
);
  logic [6:0] R_TYPE;
  logic [6:0] LW;
  logic [6:0] SW;
  logic [6:0] RTypeI;
  logic [6:0] BR;
  logic [6:0] JAL;
  logic [6:0] JALR;
  logic [6:0] LUI;
  logic [6:0] AUIPC;

  assign R_TYPE = 7'b0110011;
  assign LW = 7'b0000011;
  assign SW = 7'b0100011;
  assign RTypeI = 7'b0010011;
  assign BR = 7'b1100011;
  assign JAL = 7'b1101111;
  assign JALR = 7'b1100111;
  assign LUI = 7'b0110111;
  assign AUIPC = 7'b0010111;
  assign ALUSrc = ((Opcode == LW || Opcode == SW) || Opcode == RTypeI) || Opcode == JALR;
  assign MemtoReg = Opcode == LW;
  assign RegWrite = (((((Opcode == R_TYPE || Opcode == LW) || Opcode == RTypeI) || Opcode == JAL) || Opcode == JALR) || Opcode == LUI) || Opcode == AUIPC;
  assign MemRead = Opcode == LW;
  assign MemWrite = Opcode == SW;
  assign ALUOp[0] = (Opcode == BR || Opcode == JAL) || Opcode == LUI;
  assign ALUOp[1] = ((Opcode == R_TYPE || Opcode == JAL) || Opcode == LUI) || Opcode == RTypeI;
  assign Branch = Opcode == BR || Opcode == JAL;
  assign JalrSel = Opcode == JALR;
  assign RWSel[0] = (Opcode == JALR || Opcode == JAL) || Opcode == AUIPC;
  assign RWSel[1] = Opcode == LUI || Opcode == AUIPC;
endmodule
