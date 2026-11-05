`timescale 1ns/1ps
module tb_sync_fifo;
    logic clk=0, rst=1, wr_en=0, rd_en=0;
    logic [7:0] din=0, dout;
    logic full, empty;
    logic [2:0] count;
    always #5 clk=~clk;
    sync_fifo #(.WIDTH(8),.DEPTH(4)) dut(.*);

    task tick; begin @(negedge clk); end endtask
    task push(input logic [7:0] value);
      begin din=value; wr_en=1; rd_en=0; tick(); wr_en=0; end
    endtask
    task pop_expect(input logic [7:0] value);
      begin
        if (empty) $fatal(1,"FIFO unexpectedly empty");
        if (dout !== value) $fatal(1,"FIFO data mismatch expected=%0h got=%0h",value,dout);
        rd_en=1; wr_en=0; tick(); rd_en=0;
      end
    endtask

    initial begin
      repeat(2) tick(); rst=0; tick();
      if (!empty || full || count!=0) $fatal(1,"bad reset state");
      push(8'h11); push(8'h22); push(8'h33); push(8'h44);
      if (!full || count!=4) $fatal(1,"FIFO did not become full");
      push(8'h55); // rejected while full
      if (!full || count!=4) $fatal(1,"write while full changed count");
      pop_expect(8'h11); pop_expect(8'h22); pop_expect(8'h33); pop_expect(8'h44);
      if (!empty || count!=0) $fatal(1,"FIFO did not become empty");
      push(8'hA5); pop_expect(8'hA5);
      $display("PASS: synchronous FIFO directed tests");
      $finish;
    end
endmodule
