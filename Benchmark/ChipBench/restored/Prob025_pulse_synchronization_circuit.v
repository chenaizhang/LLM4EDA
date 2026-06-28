module RefModule (
  input wire  clk_fast,
  input wire  clk_slow,
  input wire  rst_n,
  input wire  data_in,
  output wire  data_out
);
  reg Q_fast;
  reg Q_buff0;
  reg Q_buff1;
  reg Q_slow;

  always @(posedge clk_fast or negedge rst_n) begin
    if (~rst_n)
      Q_fast <= 'd0;
    else
      if (data_in)
        Q_fast <= ~Q_fast;
      else
        if (~data_in)
          Q_fast <= Q_fast;
  end
  always @(posedge clk_slow or negedge rst_n) begin
    if (~rst_n) begin
      Q_buff0 <= 'd0;
      Q_buff1 <= 'd0;
    end else begin
      Q_buff0 <= Q_fast;
      Q_buff1 <= Q_buff0;
    end
  end
  always @(posedge clk_slow or negedge rst_n) begin
    if (~rst_n)
      Q_slow <= 'd0;
    else
      Q_slow <= Q_buff1;
  end

  assign data_out = Q_buff1 ^ Q_slow;
endmodule
