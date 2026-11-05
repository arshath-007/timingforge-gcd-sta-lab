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
    integer random_cases = 0;
    integer zero_input_cases = 0;
    integer equal_operand_cases = 0;
    integer both_even_cases = 0;
    integer one_even_cases = 0;
    integer both_odd_cases = 0;
    integer high_bit_cases = 0;
    integer gcd_one_cases = 0;
    integer gcd_nontrivial_cases = 0;
    integer combined_le32 = 0, combined_33_64 = 0, combined_gt64 = 0;
    integer split_le32 = 0, split_33_64 = 0, split_gt64 = 0;
    integer initial_seed = 32'h5446_2026;
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
            if ((a == 0) || (b == 0)) zero_input_cases = zero_input_cases + 1;
            if (a == b) equal_operand_cases = equal_operand_cases + 1;
            if (!a[0] && !b[0]) both_even_cases = both_even_cases + 1;
            else if (a[0] && b[0]) both_odd_cases = both_odd_cases + 1;
            else one_even_cases = one_even_cases + 1;
            if (a[WIDTH-1] || b[WIDTH-1]) high_bit_cases = high_bit_cases + 1;
            if (expected == 1) gcd_one_cases = gcd_one_cases + 1;
            else if (expected > 1) gcd_nontrivial_cases = gcd_nontrivial_cases + 1;
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

            // Completion was sampled while done was high in the loop above.
            // At task exit it may already have deasserted on the next clock.
            if (busy_combined || busy_split) $fatal(1, "busy remained asserted after done");
            if (done_combined || done_split) begin
                @(negedge clk);
                if (done_combined || done_split) $fatal(1, "done pulse exceeded one cycle");
            end
            total_combined_cycles = total_combined_cycles + combined_latency;
            total_split_cycles = total_split_cycles + split_latency;
            if (combined_latency > max_combined_cycles) max_combined_cycles = combined_latency;
            if (split_latency > max_split_cycles) max_split_cycles = split_latency;
            if (combined_latency <= 32) combined_le32 = combined_le32 + 1;
            else if (combined_latency <= 64) combined_33_64 = combined_33_64 + 1;
            else combined_gt64 = combined_gt64 + 1;
            if (split_latency <= 32) split_le32 = split_le32 + 1;
            else if (split_latency <= 64) split_33_64 = split_33_64 + 1;
            else split_gt64 = split_gt64 + 1;
            cases = cases + 1;
        end
    endtask

    integer i;
    reg [WIDTH-1:0] ra, rb;
    initial begin
        repeat (3) @(negedge clk);
        rst = 1'b0;
        // Keep the random corpus reproducible across repeated runs with the same simulator.
        seed = initial_seed;

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
            ra = $random(seed);
            rb = $random(seed);
            // Deterministic constraint classes over seeded random base values.
            case (i % 5)
                0: begin ra = ra | 32'h0000_0001; rb = rb | 32'h0000_0001; end // odd/odd
                1: begin ra = ra & 32'hffff_fffe; rb = rb | 32'h0000_0001; end // even/odd
                2: begin ra = ra & 32'hffff_fffe; rb = rb & 32'hffff_fffe; end // even/even
                3: begin ra = ra | 32'h8000_0000; rb = rb | 32'h8000_0000; end // high-bit operands
                4: rb = ra; // equal operands
                default: begin end
            endcase
            check_case(ra, rb);
            random_cases = random_cases + 1;
        end

        if (random_cases != 250 || zero_input_cases == 0 || equal_operand_cases == 0 ||
            both_even_cases == 0 || one_even_cases == 0 || both_odd_cases == 0 ||
            high_bit_cases == 0 || gcd_one_cases == 0 || gcd_nontrivial_cases == 0)
            $fatal(1, "coverage requirement not met");
        $display("PASS: %0d cases checked on both architectures", cases);
        $display("SEED: 0x%08x RANDOM_CASES: %0d", initial_seed, random_cases);
        $display("COVERAGE: zero=%0d equal=%0d both_even=%0d one_even=%0d both_odd=%0d high_bit=%0d gcd_one=%0d gcd_nontrivial=%0d",
            zero_input_cases, equal_operand_cases, both_even_cases, one_even_cases, both_odd_cases,
            high_bit_cases, gcd_one_cases, gcd_nontrivial_cases);
        $display("LATENCY_BINS: combined_le32=%0d combined_33_64=%0d combined_gt64=%0d split_le32=%0d split_33_64=%0d split_gt64=%0d",
            combined_le32, combined_33_64, combined_gt64, split_le32, split_33_64, split_gt64);
        $display("LATENCY: combined_avg=%.2f cycles combined_max=%0d cycles split_avg=%.2f cycles split_max=%0d cycles", 1.0*total_combined_cycles/cases, max_combined_cycles, 1.0*total_split_cycles/cases, max_split_cycles);
        $finish;
    end
endmodule
