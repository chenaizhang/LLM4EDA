module RefModule #(
  parameter DATA_WIDTH = 32,
  parameter ADDRESS_WIDTH = 5,
  parameter NUM_REGS = 32
) (
  input wire  clk,
  input wire  rst,
  input wire  rg_wrt_en,
  input wire [ADDRESS_WIDTH-1:0] rg_wrt_dest,
  input wire [ADDRESS_WIDTH-1:0] rg_rd_addr1,
  input wire [ADDRESS_WIDTH-1:0] rg_rd_addr2,
  input wire [DATA_WIDTH-1:0] rg_wrt_data,
  output logic [DATA_WIDTH-1:0] rg_rd_data1,
  output logic [DATA_WIDTH-1:0] rg_rd_data2
);
  logic [DATA_WIDTH-1:0] register_file [NUM_REGS-1:0];
  integer i;

  always @(posedge clk) begin
    if (rst == 1'b1)
      for (i = 0; i < NUM_REGS; i = i + 1) begin
        register_file [i] <= 0;
      end
    else
      if (rst == 1'b0 && rg_wrt_en == 1'b1)
        register_file [ rg_wrt_dest ] <= rg_wrt_data;
  end

  assign rg_rd_data1 = register_file[rg_rd_addr1];
  assign rg_rd_data2 = register_file[rg_rd_addr2];
endmodule
