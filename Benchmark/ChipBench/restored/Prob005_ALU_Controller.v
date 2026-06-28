module RefModule (
  input logic [1:0] ALUOp,
  input logic [6:0] Funct7,
  input logic [2:0] Funct3,
  output logic [3:0] Operation
);

  assign Operation[0] = (((((ALUOp == 2'b10 && Funct3 == 3'b110 || ALUOp == 2'b10 && Funct3 == 3'b100) || (ALUOp == 2'b10 && Funct3 == 3'b101) && Funct7 == 7'b0000000) || (ALUOp == 2'b10 && Funct3 == 3'b101) && Funct7 == 7'b0100000) || ALUOp == 2'b01 && Funct3 == 3'b001) || ALUOp == 2'b01 && Funct3 == 3'B101) || ALUOp == 2'b01 && Funct3 == 3'b111;
  assign Operation[1] = (((((((ALUOp == 2'b00 || ALUOp == 2'b10 && Funct3 == 3'b000) || ALUOp == 2'b10 && Funct3 == 3'b100) || (ALUOp == 2'b10 && Funct7 == 7'b0100000) && Funct3 == 3'b000) || (ALUOp == 2'b10 && Funct3 == 3'b101) && Funct7 == 7'b0100000) || ALUOp == 2'b11) || ALUOp == 2'b10 && Funct3 == 3'b011) || ALUOp == 2'b01 && Funct3 == 3'b110) || ALUOp == 2'b01 && Funct3 == 3'b111;
  assign Operation[2] = (((((((((ALUOp == 2'b10 && Funct3 == 3'b101) && Funct7 == 7'b0000000 || (ALUOp == 2'b10 && Funct3 == 3'b101) && Funct7 == 7'b0100000) || ALUOp == 2'b10 && Funct3 == 3'b001) || (ALUOp == 2'b10 && Funct7 == 7'b0100000) && Funct3 == 3'b000) || ALUOp == 2'b10 && Funct3 == 3'b010) || ALUOp == 2'b10 && Funct3 == 3'b011) || ALUOp == 2'b01 && Funct3 == 3'b110) || ALUOp == 2'b01 && Funct3 == 3'b100) || ALUOp == 2'b01 && Funct3 == 3'B101) || ALUOp == 2'b01 && Funct3 == 3'b111;
  assign Operation[3] = ((ALUOp == 2'b01 || ALUOp == 2'b11) || ALUOp == 2'b10 && Funct3 == 3'b010) || ALUOp == 2'b10 && Funct3 == 3'b011;
endmodule
