module RefModule #(
  parameter WIDTH = 8,
  parameter DEPTH = 16
) (
  input wire  clk,
  input wire  rst_n,
  input wire  winc,
  input wire  rinc,
  input wire [WIDTH-1:0] wdata,
  output wire  wfull,
  output wire  rempty,
  output wire [WIDTH-1:0] rdata
);
  reg [DP_WD   :0] waddr;
  wire wenc;
  wire waddr_d_h;
  wire [DP_WD -1:0] waddr_d_l;
  reg [DP_WD   :0] raddr;
  wire renc;
  wire raddr_d_h;
  wire [DP_WD -1:0] raddr_d_l;
  wire [DP_WD :0] fifo_cnt = (waddr[DP_WD] == raddr[DP_WD]) ? waddr[DP_WD-1:0] - raddr[DP_WD-1:0]:
				          (waddr[DP_WD-1:0] + DEPTH - raddr[DP_WD-1:0]);
  localparam DP_WD = $clog2(DEPTH);

  always @(posedge clk or negedge rst_n) begin
    if (~rst_n)
      waddr <= 0;
    else
      if (wenc)
        waddr <= {waddr_d_h, waddr_d_l};
  end
  always @(posedge clk or negedge rst_n) begin
    if (~rst_n)
      raddr <= 0;
    else
      if (renc)
        raddr <= {raddr_d_h, raddr_d_l};
  end

  assign wenc = winc & !wfull;
  assign waddr_d_h = (waddr[DP_WD-1:0] == DEPTH - 1 ? ~waddr[DP_WD] : waddr[DP_WD]);
  assign waddr_d_l = (waddr[DP_WD-1:0] == DEPTH - 1 ? 0 : waddr[DP_WD-1:0] + 1);
  assign renc = rinc & !rempty;
  assign raddr_d_h = (raddr[DP_WD-1:0] == DEPTH - 1 ? ~raddr[DP_WD] : raddr[DP_WD]);
  assign raddr_d_l = (raddr[DP_WD-1:0] == DEPTH - 1 ? 0 : raddr[DP_WD-1:0] + 1);
  assign rempty = fifo_cnt == 0;
  assign wfull = fifo_cnt == DEPTH;

  dual_port_RAM #(
    .DEPTH(DEPTH),
    .WIDTH(WIDTH)
  ) u_ram (
    .wclk(clk),
    .wenc(wenc),
    .waddr(waddr[$clog2(DEPTH)-1:0]),
    .wdata(wdata),
    .rclk(clk),
    .renc(renc),
    .raddr(raddr[$clog2(DEPTH)-1:0]),
    .rdata(rdata)
  );
endmodule

module dual_port_RAM #(
  parameter DEPTH = 16,
  parameter WIDTH = 8
) (
  input wire  wclk,
  input wire  wenc,
  input wire [$clog2(DEPTH)-1:0] waddr,
  input wire [WIDTH-1:0] wdata,
  input wire  rclk,
  input wire  renc,
  input wire [$clog2(DEPTH)-1:0] raddr,
  output reg [WIDTH-1:0] rdata
);
  reg [WIDTH-1:0] RAM_MEM [0:DEPTH-1];

  always @(posedge wclk) begin
    if (wenc)
      RAM_MEM[waddr] <= wdata;
  end
  always @(posedge rclk) begin
    if (renc)
      rdata <= RAM_MEM[raddr];
  end
endmodule
