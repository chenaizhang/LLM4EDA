module RefModule (
  input wire [1:0] d0,
  input wire [1:0] d1,
  input wire [1:0] d2,
  input wire [1:0] d3,
  input wire [1:0] sel,
  output wire [1:0] mux_out
);

  assign mux_out = (sel[1] ? (sel[0] ? d3 : d2) : (sel[0] ? d1 : d0));
endmodule
