`timescale 1ns/1ps

module tb_gcd_compare;
    localparam integer WIDTH = 32;
    logic clk = 1'b0;
    logic rst = 1'b1;
    logic start = 1'b0;
    logic [WIDTH-1:0] a_in = '0, b_in = '0;
    logic [WIDTH-1:0] gcd_combined, gcd_split;
    logic busy_combined, done_combined, busy_split, done_split;
    integer cases = 0;

    always #5 clk = ~clk;

    gcd_binary_combined #(.WIDTH(WIDTH)) u_combined (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_combined), .busy(busy_combined), .done(done_combined)
    );

    gcd_binary_split #(.WIDTH(WIDTH)) u_split (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_split), .busy(busy_split), .done(done_split)
    );

    function automatic [WIDTH-1:0] gcd_ref(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        reg [WIDTH-1:0] t;
        begin
            while (b != 0) begin
                t = a % b;
                a = b;
                b = t;
            end
            gcd_ref = a;
        end
    endfunction

    task automatic check_case(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        reg [WIDTH-1:0] expected;
        reg combined_seen;
        reg split_seen;
        integer cycles;
        begin
            expected = gcd_ref(a, b);
            combined_seen = 1'b0;
            split_seen = 1'b0;
            @(negedge clk);
            a_in = a;
            b_in = b;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            cycles = 0;
            while ((!combined_seen || !split_seen) && cycles < 2000) begin
                if (done_combined) begin
                    combined_seen = 1'b1;
                    if (gcd_combined !== expected) begin
                        $display("COMBINED mismatch a=%0d b=%0d expected=%0d actual=%0d", a, b, expected, gcd_combined);
                        $fatal(1);
                    end
                end
                if (done_split) begin
                    split_seen = 1'b1;
                    if (gcd_split !== expected) begin
                        $display("SPLIT mismatch a=%0d b=%0d expected=%0d actual=%0d", a, b, expected, gcd_split);
                        $fatal(1);
                    end
                end
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!combined_seen || !split_seen) begin
                $display("TIMEOUT a=%0d b=%0d combined_done=%b split_done=%b", a, b, combined_seen, split_seen);
                $fatal(1);
            end
            cases = cases + 1;
        end
    endtask

    integer i;
    reg [WIDTH-1:0] ra, rb;
    initial begin
        repeat (3) @(negedge clk);
        rst = 1'b0;

        check_case(0, 0);
        check_case(0, 99);
        check_case(72, 0);
        check_case(48, 18);
        check_case(270, 192);
        check_case(32'h8000_0000, 32'h4000_0000);
        check_case(32'hffff_ffff, 32'h7fff_ffff);
        check_case(32'hffff_ffff, 32'hffff_ffff);

        for (i = 0; i < 250; i = i + 1) begin
            ra = {$urandom, $urandom};
            rb = {$urandom, $urandom};
            check_case(ra, rb);
        end

        $display("PASS: %0d cases checked on both architectures", cases);
        $finish;
    end
endmodule
