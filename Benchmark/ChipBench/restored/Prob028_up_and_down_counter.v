module RefModule (
  input wire  clk,
  input wire  rst_n,
  input wire  mode,
  output reg [3:0] number,
  output reg  zero
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      zero <= 1'd0;
    else
      if (number == 4'd0)
        zero <= 1'b1;
      else
        zero <= 1'b0;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      number <= 4'b0;
    else
      if (mode) begin
        if (number == 9)
          number <= 0;
        else
          number <= number + 1'd1;
      end else begin
        if (!mode) begin
          if (number == 0)
            number <= 9;
          else
            number <= number - 1'd1;
        end else begin
          number <= number;
        end
      end
  end
endmodule
