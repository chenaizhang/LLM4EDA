module RefModule (
  input wire  clk,
  input wire  rst,
  input wire  data,
  output reg  flag
);
  reg [2:0] current_state;
  reg [2:0] next_state;
  parameter S0 = 'd0;
  parameter S1 = 'd1;
  parameter S2 = 'd2;
  parameter S3 = 'd3;
  parameter S4 = 'd4;

  always @(posedge clk or negedge rst) begin
    if (rst == 1'b0)
      current_state <= S0;
    else
      current_state <= next_state;
  end
  always @(*) begin
    case (current_state)
      S0: begin
        next_state = (data ? S1 : S0);
        flag = 1'b0;
      end
      S1: begin
        next_state = (data ? S2 : S1);
        flag = 1'b0;
      end
      S2: begin
        next_state = (data ? S3 : S2);
        flag = 1'b0;
      end
      S3: begin
        next_state = (data ? S4 : S3);
        flag = 1'b0;
      end
      S4: begin
        next_state = (data ? S1 : S0);
        flag = 1'b1;
      end
      default: begin
        next_state = S0;
        flag = 1'b0;
      end
    endcase
  end
endmodule
