module RefModule (
  input wire  clk,
  input wire  rst_n,
  input wire  a,
  output wire  match
);
  reg [8:0] a_tem;
  reg match_f;
  reg match_b;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      match_f <= 1'b0;
    else
      if (a_tem[8:6] == 3'b011)
        match_f <= 1'b1;
      else
        match_f <= 1'b0;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      match_b <= 1'b0;
    else
      if (a_tem[2:0] == 3'b110)
        match_b <= 1'b1;
      else
        match_b <= 1'b0;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      a_tem <= 9'b0;
    else
      a_tem <= {a_tem[7:0], a};
  end

  assign match = match_b && match_f;
endmodule
