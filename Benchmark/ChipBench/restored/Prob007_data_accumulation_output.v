module RefModule (
  input wire  clk,
  input wire  rst_n,
  input wire [7:0] data_in,
  input wire  valid_a,
  input wire  ready_b,
  output wire  ready_a,
  output reg  valid_b,
  output reg [9:0] data_out
);
  reg [1:0] data_cnt;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      data_cnt <= 'd0;
    else
      if (valid_a && ready_a)
        data_cnt <= (data_cnt == 2'd3 ? 'd0 : data_cnt + 1'd1);
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      valid_b <= 'd0;
    else
      if ((data_cnt == 2'd3 && valid_a) && ready_a)
        valid_b <= 1'd1;
      else
        if (valid_b && ready_b)
          valid_b <= 1'd0;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      data_out <= 'd0;
    else
      if (((ready_b && valid_a) && ready_a) && data_cnt == 2'd0)
        data_out <= data_in;
      else
        if (valid_a && ready_a)
          data_out <= data_out + data_in;
  end

  assign ready_a = !valid_b | ready_b;
endmodule
