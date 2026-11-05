// Bounded sequential miter: architecture equivalence plus an independent GCD oracle.
// The symbolic input space is exhaustive for WIDTH=3 only.
module gcd_equiv_formal;
    localparam integer WIDTH = 3;

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
    reg [WIDTH-1:0] expected_gcd;

    reg combined_seen = 0;
    reg split_seen = 0;
    reg [WIDTH-1:0] combined_result = 0;
    reg [WIDTH-1:0] split_result = 0;

    // Independent Euclidean specification. This is intentionally separate
    // from the binary-GCD datapaths under comparison.
    reg [WIDTH-1:0] reference_a, reference_b, reference_remainder;
    integer reference_step;
    // Fixed-depth unrolling avoids unsupported dynamic function evaluation in
    // the pinned Yosys 0.33 formal frontend. WIDTH*2 iterations exceed the
    // maximum Euclidean remainder steps for the exhaustive 3-bit domain.
    always @* begin
        reference_a = a_in;
        reference_b = b_in;
        reference_remainder = 0;
        for (reference_step = 0; reference_step < WIDTH*2; reference_step = reference_step + 1) begin
            if (reference_b != 0) begin
                reference_remainder = reference_a % reference_b;
                reference_a = reference_b;
                reference_b = reference_remainder;
            end
        end
        expected_gcd = reference_a;
    end

    gcd_binary_combined #(.WIDTH(WIDTH)) u_combined (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_combined), .busy(busy_combined), .done(done_combined)
    );

    gcd_binary_split #(.WIDTH(WIDTH)) u_split (
        .clk(clk), .rst(rst), .start(start), .a_in(a_in), .b_in(b_in),
        .gcd_out(gcd_split), .busy(busy_split), .done(done_split)
    );

    initial cycle = 0;

    always @(posedge clk) begin
        if (cycle < 7'd12)
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
                assert(gcd_combined == expected_gcd);
                combined_seen <= 1;
                combined_result <= gcd_combined;
            end
            if (done_split) begin
                assert(!split_seen);
                assert(!busy_split);
                assert(gcd_split == expected_gcd);
                split_seen <= 1;
                split_result <= gcd_split;
            end
            if (combined_seen && split_seen)
                assert(combined_result == split_result);
            if (cycle == 7'd12) begin
                assert(combined_seen);
                assert(split_seen);
            end
        end
    end
endmodule
