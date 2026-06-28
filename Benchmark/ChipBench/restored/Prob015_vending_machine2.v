module RefModule (
  input wire  clk,
  input wire  rst,
  input wire  d1,
  input wire  d2,
  input wire  sel,
  output reg  out1,
  output reg  out2,
  output reg  out3
);
  reg [2:0] state;
  reg [2:0] nstate;
  parameter S0 = 0;
  parameter S0_5 = 1;
  parameter S1 = 2;
  parameter S1_5 = 3;
  parameter S2 = 4;
  parameter S2_5 = 5;
  parameter S3 = 6;

  always @(posedge clk or negedge rst) begin
    if (~rst)
      state <= 0;
    else
      state <= nstate;
  end
  always @(*) begin
    case (state)
      S0: nstate = (d1 ? S0_5 : (d2 ? S1 : nstate));
      S0_5: nstate = (d1 ? S1 : (d2 ? S1_5 : nstate));
      S1: nstate = (d1 ? S1_5 : (d2 ? S2 : nstate));
      S1_5: nstate = (~sel ? S0 : (d1 ? S2 : (d2 ? S2_5 : nstate)));
      S2: nstate = (~sel ? S0 : (d1 ? S2_5 : (d2 ? S3 : nstate)));
      default: nstate = S0;
    endcase
  end
  always @(*) begin
    if (~rst)
      {out1, out2, out3} = 3'b000;
    else
      case (state)
        S0, S0_5, S1: {out1, out2, out3} = 0;
        S1_5: {out1, out2, out3} = (~sel ? 3'b100 : 3'b000);
        S2: {out1, out2, out3} = (~sel ? 3'b101 : 3'b000);
        S2_5: {out1, out2, out3} = (~sel ? 3'b101 : 3'b010);
        S3: {out1, out2, out3} = (~sel ? 3'b101 : 3'b011);
        default: {out1, out2, out3} = 3'b000;
      endcase
  end
endmodule
