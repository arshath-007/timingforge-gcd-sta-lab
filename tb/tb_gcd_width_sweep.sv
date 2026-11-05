`timescale 1ns/1ps

module tb_gcd_width_sweep #(
    parameter integer WIDTH = 32,
    parameter integer RANDOM_CASES = 40
);
    reg clk = 1'b0;
    reg rst = 1'b1;
    reg start = 1'b0;
    reg [WIDTH-1:0] a_in = '0;
    reg [WIDTH-1:0] b_in = '0;
    wire [WIDTH-1:0] gcd_combined, gcd_split;
    wire busy_combined, done_combined, busy_split, done_split;
    integer seed = 32'h5446_2026;
    integer i;

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
        reg [WIDTH-1:0] remainder;
        begin
            while (b != 0) begin
                remainder = a % b;
                a = b;
                b = remainder;
            end
            gcd_ref = a;
        end
    endfunction

    task automatic check_case(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        reg [WIDTH-1:0] expected;
        reg combined_seen, split_seen;
        integer cycles;
        begin
            expected = gcd_ref(a, b);
            combined_seen = 1'b0;
            split_seen = 1'b0;
            cycles = 0;
            @(negedge clk);
            a_in = a;
            b_in = b;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            while ((!combined_seen || !split_seen) && cycles < 10000) begin
                if (done_combined && !combined_seen) begin
                    combined_seen = 1'b1;
                    if (gcd_combined !== expected)
                        $fatal(1, "combined WIDTH=%0d a=%0d b=%0d expected=%0d actual=%0d", WIDTH, a, b, expected, gcd_combined);
                end
                if (done_split && !split_seen) begin
                    split_seen = 1'b1;
                    if (gcd_split !== expected)
                        $fatal(1, "split WIDTH=%0d a=%0d b=%0d expected=%0d actual=%0d", WIDTH, a, b, expected, gcd_split);
                end
                if (!combined_seen || !split_seen) begin
                    @(negedge clk);
                    cycles = cycles + 1;
                end
            end
            if (!combined_seen || !split_seen)
                $fatal(1, "timeout WIDTH=%0d a=%0d b=%0d", WIDTH, a, b);
            if (busy_combined || busy_split)
                $fatal(1, "busy remained high after completion WIDTH=%0d", WIDTH);
            @(negedge clk);
            if (done_combined || done_split)
                $fatal(1, "done was not a one-cycle pulse WIDTH=%0d", WIDTH);
        end
    endtask

    reg [WIDTH-1:0] random_a, random_b, high_bit, all_ones;
    initial begin
        high_bit = {1'b1, {(WIDTH-1){1'b0}}};
        all_ones = {WIDTH{1'b1}};
        repeat (3) @(negedge clk);
        rst = 1'b0;
        check_case('0, '0);
        check_case('0, all_ones);
        check_case(high_bit, '0);
        check_case(all_ones, all_ones);
        check_case(all_ones, all_ones - 1'b1);
        check_case(high_bit, high_bit >> 1);
        for (i = 0; i < RANDOM_CASES; i = i + 1) begin
            random_a = $random(seed);
            random_b = $random(seed);
            case (i % 4)
                0: begin random_a[0] = 1'b1; random_b[0] = 1'b1; end
                1: begin random_a[0] = 1'b0; random_b[0] = 1'b1; end
                2: begin random_a[0] = 1'b0; random_b[0] = 1'b0; end
                3: begin random_a[WIDTH-1] = 1'b1; random_b[WIDTH-1] = 1'b1; end
            endcase
            check_case(random_a, random_b);
        end
        $display("PASS: parameterized GCD width sweep WIDTH=%0d cases=%0d", WIDTH, RANDOM_CASES + 6);
        $finish;
    end
endmodule
