module RefModule (
  input wire  clk,
  input wire  rst_n,
  output reg  data
);
  reg [5:0] q;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      q <= 6'b001011;
    else
      q <= {q[4:0], q[5]};
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      data <= 1'd0;
    else
      data <= q[5];
  end
endmodule
