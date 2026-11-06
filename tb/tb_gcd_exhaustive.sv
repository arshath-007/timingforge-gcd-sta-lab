// Exhaustive 8-bit transaction-level check against an independent Euclidean GCD.
module tb_gcd_exhaustive;
    localparam integer WIDTH = 8;
    localparam integer MAX_CYCLES = 120;

    reg clk = 0;
    reg rst = 1;
    reg start = 0;
    reg [WIDTH-1:0] a_in = 0;
    reg [WIDTH-1:0] b_in = 0;
    wire [WIDTH-1:0] gcd_combined, gcd_split;
    wire busy_combined, done_combined, busy_split, done_split;

    integer i, j, k;
    integer combined_done_count, split_done_count;
    integer checked_pairs = 0;
    reg [WIDTH-1:0] expected;
    reg [WIDTH-1:0] combined_result, split_result;

    always #5 clk = ~clk;

    gcd_binary_combined #(.WIDTH(WIDTH)) u_combined (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_combined), .busy(busy_combined), .done(done_combined)
    );
    gcd_binary_split #(.WIDTH(WIDTH)) u_split (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_split), .busy(busy_split), .done(done_split)
    );

    function automatic [WIDTH-1:0] gcd_spec(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        reg [WIDTH-1:0] x, y, temp;
        integer step;
        begin
            x = a;
            y = b;
            for (step = 0; step < (2 * WIDTH); step = step + 1) begin
                if (y != 0) begin
                    temp = x % y;
                    x = y;
                    y = temp;
                end
            end
            gcd_spec = x;
        end
    endfunction

    task automatic observe_done;
        begin
            if (done_combined) begin
                combined_done_count = combined_done_count + 1;
                combined_result = gcd_combined;
                if (busy_combined !== 1'b0)
                    $fatal(1, "combined busy remained high at done for (%0d,%0d)", a_in, b_in);
            end
            if (done_split) begin
                split_done_count = split_done_count + 1;
                split_result = gcd_split;
                if (busy_split !== 1'b0)
                    $fatal(1, "split busy remained high at done for (%0d,%0d)", a_in, b_in);
            end
        end
    endtask

    initial begin
        for (i = 0; i < (1 << WIDTH); i = i + 1) begin
            for (j = 0; j < (1 << WIDTH); j = j + 1) begin
                a_in = i[WIDTH-1:0];
                b_in = j[WIDTH-1:0];
                expected = gcd_spec(a_in, b_in);
                combined_done_count = 0;
                split_done_count = 0;
                combined_result = '0;
                split_result = '0;

                rst = 1'b1;
                start = 1'b0;
                @(negedge clk);
                rst = 1'b0;
                start = 1'b1;
                @(posedge clk);
                #1;
                observe_done();
                @(negedge clk);
                start = 1'b0;

                for (k = 0; k < MAX_CYCLES; k = k + 1) begin
                    @(posedge clk);
                    #1;
                    observe_done();
                end

                if (combined_done_count != 1 || split_done_count != 1)
                    $fatal(1, "completion count mismatch for (%0d,%0d): combined=%0d split=%0d",
                           a_in, b_in, combined_done_count, split_done_count);
                if (combined_result !== expected || split_result !== expected)
                    $fatal(1, "GCD mismatch for (%0d,%0d): expected=%0d combined=%0d split=%0d",
                           a_in, b_in, expected, combined_result, split_result);
                checked_pairs = checked_pairs + 1;
            end
        end
        $display("EXHAUSTIVE_GCD_PASS width=%0d pairs=%0d", WIDTH, checked_pairs);
        $finish;
    end
endmodule
