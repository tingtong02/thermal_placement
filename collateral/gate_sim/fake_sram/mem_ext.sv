module mem_ext(
  input  [11:0]  RW0_addr,
  input          RW0_en,
  input          RW0_clk,
  input          RW0_wmode,
  input  [127:0] RW0_wdata,
  output reg [127:0] RW0_rdata,
  input  [15:0]  RW0_wmask
);
  reg [127:0] mem [0:4095];
  integer i;

  initial begin
    RW0_rdata = 128'b0;
    for (i = 0; i < 4096; i = i + 1) begin
      mem[i] = 128'b0;
    end
  end

  always @(posedge RW0_clk) begin
    if (RW0_en) begin
      if (RW0_wmode) begin
        for (i = 0; i < 16; i = i + 1) begin
          if (RW0_wmask[i]) begin
            mem[RW0_addr][i*8 +: 8] <= RW0_wdata[i*8 +: 8];
          end
        end
        RW0_rdata <= mem[RW0_addr];
      end else begin
        RW0_rdata <= mem[RW0_addr];
      end
    end
  end
endmodule
