// Bounded sequential equivalence miter for all 3-bit input pairs.
// The proof compares transaction results, not cycle-by-cycle latency.
module gcd_equiv_formal #(parameter integer WIDTH = 3);
    localparam integer MAX_CYCLES = (2 * ((1 << WIDTH) - 2)) + 4;

    (* gclk *) reg clk = 0;
    (* anyconst *) reg [WIDTH-1:0] a_in;
    (* anyconst *) reg [WIDTH-1:0] b_in;

    reg [6:0] cycle = 0;
    wire rst = (cycle == 0);
    wire start = (cycle == 1);

    wire [WIDTH-1:0] gcd_combined;
    wire [WIDTH-1:0] gcd_split;
    wire busy_combined, done_combined;
    wire busy_split, done_split;

    reg combined_seen = 0;
    reg split_seen = 0;
    reg [WIDTH-1:0] combined_result = 0;
    reg [WIDTH-1:0] split_result = 0;

    gcd_binary_combined #(.WIDTH(WIDTH)) u_combined (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_combined), .busy(busy_combined), .done(done_combined)
    );

    gcd_binary_split #(.WIDTH(WIDTH)) u_split (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_split), .busy(busy_split), .done(done_split)
    );

    function automatic [WIDTH-1:0] gcd_spec(input [WIDTH-1:0] a, input [WIDTH-1:0] b);
        reg [WIDTH-1:0] x, y;
        integer step;
        begin
            x = a;
            y = b;
            // Independent subtractive Euclidean reference. For WIDTH-bit
            // operands, at most (2**WIDTH - 1) nonzero subtractions are needed.
            for (step = 0; step < ((1 << WIDTH) + 1); step = step + 1) begin
                if (x == 0)
                    x = y;
                else if (y == 0)
                    y = x;
                else if (x > y)
                    x = x - y;
                else if (y > x)
                    y = y - x;
            end
            gcd_spec = x;
        end
    endfunction

    initial cycle = 0;

    always @(posedge clk) begin
        if (cycle < MAX_CYCLES)
            cycle <= cycle + 1'b1;
    end

    always @(posedge clk) begin
        if (rst) begin
            combined_seen <= 0;
            split_seen <= 0;
            combined_result <= 0;
            split_result <= 0;
        end else begin
            if (done_combined) begin
                assert(!combined_seen);
                assert(!busy_combined);
                combined_seen <= 1;
                combined_result <= gcd_combined;
                assert(gcd_combined == gcd_spec(a_in, b_in));
            end
            if (done_split) begin
                assert(!split_seen);
                assert(!busy_split);
                split_seen <= 1;
                split_result <= gcd_split;
                assert(gcd_split == gcd_spec(a_in, b_in));
            end
            if (combined_seen && split_seen)
                assert(combined_result == split_result);
            if (cycle == MAX_CYCLES) begin
                assert(combined_seen);
                assert(split_seen);
            end
        end
    end
endmodule
