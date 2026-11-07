`timescale 1ns/1ps

module gcd_protocol_sva (
    input logic clk,
    input logic rst,
    input logic busy,
    input logic done
);
    property done_is_one_cycle;
        @(posedge clk) disable iff (rst) done |=> !done;
    endproperty
    property done_implies_idle;
        @(posedge clk) disable iff (rst) done |-> !busy;
    endproperty
    assert property (done_is_one_cycle)
        else $error("done must be a one-cycle pulse");
    assert property (done_implies_idle)
        else $error("busy must be low when done is asserted");
endmodule

module tb_gcd_sva;
    localparam integer WIDTH = 32;
    logic clk = 1'b0;
    logic rst = 1'b1;
    logic start = 1'b0;
    logic [WIDTH-1:0] a_in = '0;
    logic [WIDTH-1:0] b_in = '0;
    wire [WIDTH-1:0] gcd_combined, gcd_split;
    wire busy_combined, done_combined, busy_split, done_split;

    always #5 clk = ~clk;

    gcd_binary_combined #(.WIDTH(WIDTH)) u_combined (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_combined), .busy(busy_combined), .done(done_combined)
    );
    gcd_binary_split #(.WIDTH(WIDTH)) u_split (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_split), .busy(busy_split), .done(done_split)
    );

    gcd_protocol_sva combined_properties (
        .clk(clk), .rst(rst), .busy(busy_combined), .done(done_combined)
    );
    gcd_protocol_sva split_properties (
        .clk(clk), .rst(rst), .busy(busy_split), .done(done_split)
    );

    task automatic transact(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        reg seen_combined, seen_split;
        integer cycles;
        begin
            seen_combined = 1'b0;
            seen_split = 1'b0;
            cycles = 0;
            @(negedge clk);
            a_in = a;
            b_in = b;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            while ((!seen_combined || !seen_split) && cycles < 2000) begin
                if (done_combined) seen_combined = 1'b1;
                if (done_split) seen_split = 1'b1;
                if (!seen_combined || !seen_split) begin
                    @(negedge clk);
                    cycles = cycles + 1;
                end
            end
            if (!seen_combined || !seen_split)
                $fatal(1, "SVA stimulus timeout a=%0d b=%0d", a, b);
            @(negedge clk);
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst = 1'b0;
        transact(0, 0);
        transact(0, 32'hffff_ffff);
        transact(32'h8000_0000, 32'h4000_0000);
        transact(32'hffff_ffff, 32'h7fff_ffff);
        transact(270, 192);
        $display("PASS: concurrent SVA protocol assertions exercised on both GCD architectures");
        $finish;
    end
endmodule
