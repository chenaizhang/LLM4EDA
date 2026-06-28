module RefModule (
  input wire [7:0] A,
  output wire [15:0] B
);

  assign B = ((A << 8) - (A << 2)) - A;
endmodule
