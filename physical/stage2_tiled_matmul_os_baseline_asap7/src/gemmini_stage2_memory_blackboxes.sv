(* blackbox *) module mem_ext(
  input  [11:0]  RW0_addr,
  input          RW0_en,
  input          RW0_clk,
  input          RW0_wmode,
  input  [127:0] RW0_wdata,
  output [127:0] RW0_rdata,
  input  [15:0]  RW0_wmask
);
endmodule

(* blackbox *) module mem_0_ext(
  input  [8:0]   R0_addr,
  input          R0_en,
  input          R0_clk,
  output [511:0] R0_data,
  input  [8:0]   W0_addr,
  input          W0_en,
  input          W0_clk,
  input  [511:0] W0_data,
  input  [63:0]  W0_mask
);
endmodule

(* blackbox *) module mem_1_ext(
  input  [12:0] RW0_addr,
  input         RW0_en,
  input         RW0_clk,
  input         RW0_wmode,
  input  [63:0] RW0_wdata,
  output [63:0] RW0_rdata,
  input  [7:0]  RW0_wmask
);
endmodule
