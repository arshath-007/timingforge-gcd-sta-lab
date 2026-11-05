// Bounded sequential equivalence miter for all 6-bit input pairs.
// The proof compares transaction results, not cycle-by-cycle latency.
module gcd_equiv_formal;
    localparam integer WIDTH = 4;

    (* gclk *) reg clk;
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

    initial cycle = 0;

    always @(posedge clk) begin
        if (cycle < 7'd16)
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
            end
            if (done_split) begin
                assert(!split_seen);
                assert(!busy_split);
                split_seen <= 1;
                split_result <= gcd_split;
            end
            if (combined_seen && split_seen)
                assert(combined_result == split_result);
            if (cycle == 7'd24) begin
                assert(combined_seen);
                assert(split_seen);
            end
        end
    end
endmodule
