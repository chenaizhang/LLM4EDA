module RefModule #(
  parameter N = 7
) (
  input wire  rst,
  input wire  clk_in,
  output wire  clk_out7
);
  reg [3:0] cnt;
  reg clkp;
  reg clkn;

  always @(posedge clk_in or negedge rst) begin
    if (!rst)
      cnt <= 'b0;
    else
      if (cnt == N - 1)
        cnt <= 'b0;
      else
        cnt <= cnt + 1'b1;
  end
  always @(posedge clk_in or negedge rst) begin
    if (!rst)
      clkp <= 1'b0;
    else
      if (cnt == N >> 1)
        clkp <= 1;
      else
        if (cnt == N - 1)
          clkp <= 0;
  end
  always @(negedge clk_in or negedge rst) begin
    if (!rst)
      clkn <= 1'b0;
    else
      if (cnt == N >> 1)
        clkn <= 1;
      else
        if (cnt == N - 1)
          clkn <= 0;
  end

  assign clk_out7 = clkp | clkn;
endmodule
