module RefModule #(
  parameter WIDTH = 8,
  parameter DEPTH = 16
) (
  input wire  wclk,
  input wire  rclk,
  input wire  wrstn,
  input wire  rrstn,
  input wire  winc,
  input wire  rinc,
  input wire [WIDTH-1:0] wdata,
  output wire  wfull,
  output wire  rempty,
  output wire [WIDTH-1:0] rdata
);
  reg [ADDR_WIDTH:0] waddr_bin;
  reg [ADDR_WIDTH:0] raddr_bin;
  wire [ADDR_WIDTH:0] waddr_gray;
  wire [ADDR_WIDTH:0] raddr_gray;
  reg [ADDR_WIDTH:0] wptr;
  reg [ADDR_WIDTH:0] rptr;
  reg [ADDR_WIDTH:0] wptr_buff;
  reg [ADDR_WIDTH:0] wptr_syn;
  reg [ADDR_WIDTH:0] rptr_buff;
  reg [ADDR_WIDTH:0] rptr_syn;
  wire wen;
  wire ren;
  wire wren;
  wire [ADDR_WIDTH-1:0] waddr;
  wire [ADDR_WIDTH-1:0] raddr;
  parameter ADDR_WIDTH = $clog2(DEPTH);

  always @(posedge wclk or negedge wrstn) begin
    if (~wrstn)
      waddr_bin <= 'd0;
    else
      if (!wfull && winc)
        waddr_bin <= waddr_bin + 1'd1;
  end
  always @(posedge rclk or negedge rrstn) begin
    if (~rrstn)
      raddr_bin <= 'd0;
    else
      if (!rempty && rinc)
        raddr_bin <= raddr_bin + 1'd1;
  end
  always @(posedge wclk or negedge wrstn) begin
    if (~wrstn)
      wptr <= 'd0;
    else
      wptr <= waddr_gray;
  end
  always @(posedge rclk or negedge rrstn) begin
    if (~rrstn)
      rptr <= 'd0;
    else
      rptr <= raddr_gray;
  end
  always @(posedge wclk or negedge wrstn) begin
    if (~wrstn) begin
      rptr_buff <= 'd0;
      rptr_syn <= 'd0;
    end else begin
      rptr_buff <= rptr;
      rptr_syn <= rptr_buff;
    end
  end
  always @(posedge rclk or negedge rrstn) begin
    if (~rrstn) begin
      wptr_buff <= 'd0;
      wptr_syn <= 'd0;
    end else begin
      wptr_buff <= wptr;
      wptr_syn <= wptr_buff;
    end
  end

  assign waddr_gray = waddr_bin ^ waddr_bin >> 1;
  assign raddr_gray = raddr_bin ^ raddr_bin >> 1;
  assign wfull = wptr == {~rptr_syn[ADDR_WIDTH:ADDR_WIDTH-1], rptr_syn[ADDR_WIDTH-2:0]};
  assign rempty = rptr == wptr_syn;
  assign wen = winc & !wfull;
  assign ren = rinc & !rempty;
  assign waddr = waddr_bin[ADDR_WIDTH-1:0];
  assign raddr = raddr_bin[ADDR_WIDTH-1:0];

  dual_port_RAM #(
    .DEPTH(DEPTH),
    .WIDTH(WIDTH)
  ) dual_port_RAM (
    .wclk(wclk),
    .wenc(wen),
    .waddr(waddr[ADDR_WIDTH-1:0]),
    .wdata(wdata),
    .rclk(rclk),
    .renc(ren),
    .raddr(raddr[ADDR_WIDTH-1:0]),
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
