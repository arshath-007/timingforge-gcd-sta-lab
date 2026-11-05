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
    integer total_combined_cycles = 0;
    integer total_split_cycles = 0;
    integer max_combined_cycles = 0;
    integer max_split_cycles = 0;
    integer seed = 32'h5446_2026;
    reg previous_done_combined = 1'b0;
    reg previous_done_split = 1'b0;

    // done must be a one-cycle pulse in each architecture.
    always @(posedge clk) begin
        if (rst) begin
            previous_done_combined <= 1'b0;
            previous_done_split <= 1'b0;
        end else begin
            if (done_combined && previous_done_combined) $fatal(1, "combined done wider than one cycle");
            if (done_split && previous_done_split) $fatal(1, "split done wider than one cycle");
            previous_done_combined <= done_combined;
            previous_done_split <= done_split;
        end
    end

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
        integer elapsed_cycles;
        integer combined_latency;
        integer split_latency;
        begin
            expected = gcd_ref(a, b);
            combined_seen = 1'b0;
            split_seen = 1'b0;
            elapsed_cycles = 0;
            combined_latency = 0;
            split_latency = 0;

            @(negedge clk);
            a_in = a;
            b_in = b;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            if (a != 0 && b != 0) begin
                if (!busy_combined || !busy_split) $fatal(1, "busy did not assert after accepted nonzero request");
            end else begin
                if (busy_combined || busy_split) $fatal(1, "zero-input request should complete without iterative busy");
            end

            // Count clock edges from accepted start until each done pulse.
            // An input containing zero can complete on the acceptance edge (0 cycles).
            while ((!combined_seen || !split_seen) && elapsed_cycles < 2000) begin
                if (!combined_seen && done_combined) begin
                    combined_seen = 1'b1;
                    combined_latency = elapsed_cycles;
                    if (gcd_combined !== expected) begin
                        $display("COMBINED mismatch a=%0d b=%0d expected=%0d actual=%0d", a, b, expected, gcd_combined);
                        $fatal(1);
                    end
                end
                if (!split_seen && done_split) begin
                    split_seen = 1'b1;
                    split_latency = elapsed_cycles;
                    if (gcd_split !== expected) begin
                        $display("SPLIT mismatch a=%0d b=%0d expected=%0d actual=%0d", a, b, expected, gcd_split);
                        $fatal(1);
                    end
                end
                if (!combined_seen || !split_seen) begin
                    @(negedge clk);
                    elapsed_cycles = elapsed_cycles + 1;
                end
            end

            if (!combined_seen || !split_seen) begin
                $display("TIMEOUT a=%0d b=%0d combined_done=%b split_done=%b", a, b, combined_seen, split_seen);
                $fatal(1);
            end

            if (busy_combined || busy_split) $fatal(1, "busy remained asserted after done");
            if (!done_combined || !done_split) $fatal(1, "done pulse was not present at completion");
            total_combined_cycles = total_combined_cycles + combined_latency;
            total_split_cycles = total_split_cycles + split_latency;
            if (combined_latency > max_combined_cycles) max_combined_cycles = combined_latency;
            if (split_latency > max_split_cycles) max_split_cycles = split_latency;
            cases = cases + 1;
        end
    endtask

    integer i;
    reg [WIDTH-1:0] ra, rb;
    initial begin
        repeat (3) @(negedge clk);
        rst = 1'b0;
        // Keep the random corpus reproducible across repeated runs with the same simulator.
        seed = $random(seed);

        check_case(0, 0);
        check_case(0, 99);
        check_case(72, 0);
        check_case(48, 18);
        check_case(270, 192);
        check_case(32'h8000_0000, 32'h4000_0000);
        check_case(32'hffff_ffff, 32'h7fff_ffff);
        check_case(32'hffff_ffff, 32'hffff_ffff);
        // Explicit high-iteration stress case; distinct adjacent odd operands.
        check_case(32'hffff_ffff, 32'hffff_fffe);

        for (i = 0; i < 250; i = i + 1) begin
            ra = {$random(seed), $random(seed)};
            rb = {$random(seed), $random(seed)};
            check_case(ra, rb);
        end

        $display("PASS: %0d cases checked on both architectures", cases);
        $display("LATENCY: combined_avg=%.2f cycles combined_max=%0d cycles split_avg=%.2f cycles split_max=%0d cycles", 1.0*total_combined_cycles/cases, max_combined_cycles, 1.0*total_split_cycles/cases, max_split_cycles);
        $finish;
    end
endmodule
