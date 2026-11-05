`timescale 1ns/1ps
module tb_mac_accumulator;
    logic clk=0,rst=1,clear=0,enable=0;
    logic signed [7:0] a=0,b=0;
    logic signed [23:0] acc;
    always #5 clk=~clk;
    mac_accumulator #(.DATA_WIDTH(8),.ACC_WIDTH(24)) dut(.*);

    task tick; begin @(negedge clk); end endtask
    initial begin
      repeat(2) tick(); rst=0; tick();
      if (acc!==0) $fatal(1,"MAC reset failed");
      a=-8'sd3; b=8'sd4; enable=1; tick();
      if (acc!==-24'sd12) $fatal(1,"MAC signed multiply failed: %0d",acc);
      a=8'sd5; b=8'sd2; tick();
      if (acc!==-24'sd2) $fatal(1,"MAC accumulate failed: %0d",acc);
      enable=0; a=8'sd7; b=8'sd7; tick();
      if (acc!==-24'sd2) $fatal(1,"MAC enable hold failed");
      clear=1; tick(); clear=0;
      if (acc!==0) $fatal(1,"MAC clear failed");
      $display("PASS: signed MAC accumulator directed tests");
      $finish;
    end
endmodule
