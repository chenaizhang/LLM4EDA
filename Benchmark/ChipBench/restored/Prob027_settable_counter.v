module RefModule (
  input wire  clk,
  input wire  rst_n,
  input wire  set,
  input wire [3:0] set_num,
  output reg [3:0] number,
  output reg  zero
);
  reg [3:0] num;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      zero <= 1'd0;
    else
      if (num == 4'd0)
        zero <= 1'b1;
      else
        zero <= 1'b0;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      num <= 4'b0;
    else
      if (set)
        num <= set_num;
      else
        num <= num + 1'd1;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      number <= 1'd0;
    else
      number <= num;
  end
endmodule
