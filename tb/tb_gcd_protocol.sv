`timescale 1ns/1ps

module tb_gcd_protocol;
    localparam integer WIDTH = 32;
    reg clk = 1'b0;
    reg rst = 1'b1;
    reg start = 1'b0;
    reg [WIDTH-1:0] a_in = '0, b_in = '0;
    wire [WIDTH-1:0] gcd_combined, gcd_split;
    wire busy_combined, done_combined, busy_split, done_split;
    integer cycles;

    always #5 clk = ~clk;

    gcd_binary_combined #(.WIDTH(WIDTH)) u_combined (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_combined), .busy(busy_combined), .done(done_combined)
    );
    gcd_binary_split #(.WIDTH(WIDTH)) u_split (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_split), .busy(busy_split), .done(done_split)
    );

    task automatic launch(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        begin
            @(negedge clk);
            a_in = a;
            b_in = b;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
        end
    endtask

    task automatic await_result(input [WIDTH-1:0] expected);
        reg seen_combined, seen_split;
        begin
            seen_combined = 1'b0;
            seen_split = 1'b0;
            cycles = 0;
            while ((!seen_combined || !seen_split) && cycles < 2000) begin
                @(posedge clk);
                #1;
                if (done_combined) begin
                    if (gcd_combined !== expected)
                        $fatal(1, "combined result mismatch expected=%0d actual=%0d", expected, gcd_combined);
                    if (busy_combined !== 1'b0)
                        $fatal(1, "combined busy high with done");
                    if (seen_combined) $fatal(1, "combined duplicate completion");
                    seen_combined = 1'b1;
                end
                if (done_split) begin
                    if (gcd_split !== expected)
                        $fatal(1, "split result mismatch expected=%0d actual=%0d", expected, gcd_split);
                    if (busy_split !== 1'b0)
                        $fatal(1, "split busy high with done");
                    if (seen_split) $fatal(1, "split duplicate completion");
                    seen_split = 1'b1;
                end
                cycles = cycles + 1;
            end
            if (!seen_combined || !seen_split)
                $fatal(1, "timeout waiting for both architectures");
            @(negedge clk);
            if (done_combined || done_split)
                $fatal(1, "done did not return low after completion");
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst = 1'b0;

        // Start a long transaction, then pulse start with different operands
        // while both engines are busy. The second request must be ignored.
        launch(32'hffff_ffff, 32'h7fff_ffff);
        repeat (3) @(negedge clk);
        if (!busy_combined || !busy_split)
            $fatal(1, "expected both architectures to be busy");
        a_in = 32'd21;
        b_in = 32'd14;
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;
        await_result(32'd1);

        // A fresh transaction after completion must be accepted normally.
        launch(32'd48, 32'd18);
        await_result(32'd6);

        // Reset in the middle of an iterative operation must abort it cleanly.
        launch(32'hffff_ffff, 32'h7fff_fffe);
        repeat (3) @(negedge clk);
        if (!busy_combined || !busy_split)
            $fatal(1, "expected busy before mid-operation reset");
        rst = 1'b1;
        @(negedge clk);
        rst = 1'b0;
        #1;
        if (busy_combined || busy_split || done_combined || done_split)
            $fatal(1, "mid-operation reset did not return both engines to idle");

        // The engines must accept a new request after reset-abort.
        launch(32'd270, 32'd192);
        await_result(32'd6);

        $display("PASS: busy-start rejection, mid-operation reset, restart and sequential transactions");
        $finish;
    end
endmodule
