module mem_0_ext(
  input  [8:0]   R0_addr,
  input          R0_en,
  input          R0_clk,
  output reg [511:0] R0_data,
  input  [8:0]   W0_addr,
  input          W0_en,
  input          W0_clk,
  input  [511:0] W0_data,
  input  [63:0]  W0_mask
);
  reg [511:0] mem [0:511];
  integer i;

  initial begin
    R0_data = 512'b0;
    for (i = 0; i < 512; i = i + 1) begin
      mem[i] = 512'b0;
    end
  end

  always @(posedge W0_clk) begin
    if (W0_en) begin
      for (i = 0; i < 64; i = i + 1) begin
        if (W0_mask[i]) begin
          mem[W0_addr][i*8 +: 8] <= W0_data[i*8 +: 8];
        end
      end
    end
  end

  always @(posedge R0_clk) begin
    if (R0_en) begin
      R0_data <= mem[R0_addr];
    end
  end
endmodule
