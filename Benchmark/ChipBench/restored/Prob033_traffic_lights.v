module RefModule (
  input wire  rst_n,
  input wire  clk,
  input wire  pass_request,
  output wire [7:0] clock,
  output reg  red,
  output reg  yellow,
  output reg  green
);
  reg [7:0] cnt;
  reg [1:0] state;
  reg p_red;
  reg p_yellow;
  reg p_green;
  parameter idle = 2'd0;
  parameter s1_red = 2'd1;
  parameter s2_green = 2'd2;
  parameter s3_yellow = 2'd3;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= idle;
      p_red <= 1'b0;
      p_green <= 1'b0;
      p_yellow <= 1'b0;
    end else begin
      case (state)
        idle: begin
          p_red <= 1'b0;
          p_green <= 1'b0;
          p_yellow <= 1'b0;
          state <= s1_red;
        end
        s1_red: begin
          p_red <= 1'b1;
          p_green <= 1'b0;
          p_yellow <= 1'b0;
          if (cnt == 3)
            state <= s2_green;
          else
            state <= s1_red;
        end
        s2_green: begin
          p_red <= 1'b0;
          p_green <= 1'b1;
          p_yellow <= 1'b0;
          if (cnt == 3)
            state <= s3_yellow;
          else
            state <= s2_green;
        end
        s3_yellow: begin
          p_red <= 1'b0;
          p_green <= 1'b0;
          p_yellow <= 1'b1;
          if (cnt == 3)
            state <= s1_red;
          else
            state <= s3_yellow;
        end
      endcase
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      cnt <= 7'd10;
    else
      if ((pass_request && green) && cnt > 10)
        cnt <= 7'd10;
      else
        if (!green && p_green)
          cnt <= 7'd60;
        else
          if (!yellow && p_yellow)
            cnt <= 7'd5;
          else
            if (!red && p_red)
              cnt <= 7'd10;
            else
              cnt <= cnt - 1;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      yellow <= 1'd0;
      red <= 1'd0;
      green <= 1'd0;
    end else begin
      yellow <= p_yellow;
      red <= p_red;
      green <= p_green;
    end
  end

  assign clock = cnt;
endmodule
