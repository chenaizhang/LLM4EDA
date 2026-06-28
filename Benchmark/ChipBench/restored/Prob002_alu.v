module RefModule #(
  parameter DATA_WIDTH = 32,
  parameter OPCODE_LENGTH = 4
) (
  input logic [DATA_WIDTH-1:0] SrcA,
  input logic [DATA_WIDTH-1:0] SrcB,
  input logic [OPCODE_LENGTH-1:0] Operation,
  output logic [DATA_WIDTH-1:0] ALUResult
);

  always_comb begin
    case (Operation)
      4'b0000: ALUResult = SrcA & SrcB;
      4'b0001: ALUResult = SrcA | SrcB;
      4'b0010: ALUResult = $signed(SrcA) + $signed(SrcB);
      4'b0011: ALUResult = SrcA ^ SrcB;
      4'b0100: ALUResult = SrcA << SrcB[4:0];
      4'b0101: ALUResult = SrcA >> SrcB[4:0];
      4'b0110: ALUResult = $signed(SrcA) - $signed(SrcB);
      4'b0111: ALUResult = $signed(SrcA) >>> SrcB[4:0];
      4'b1000: ALUResult = (SrcA == SrcB ? 1 : 0);
      4'b1001: ALUResult = (SrcA != SrcB ? 1 : 0);
      4'b1100: ALUResult = ($signed(SrcA) < $signed(SrcB) ? 1 : 0);
      4'b1101: ALUResult = ($signed(SrcA) >= $signed(SrcB) ? 1 : 0);
      4'b1110: ALUResult = (SrcA < SrcB ? 1 : 0);
      4'b1111: ALUResult = (SrcA >= SrcB ? 1 : 0);
      4'b1010: ALUResult = 1;
      default: ALUResult = 0;
    endcase
  end
endmodule
