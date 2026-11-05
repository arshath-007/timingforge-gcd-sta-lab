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
    // Exhaustive 64-entry specification table for WIDTH=3. Values are
    // generated independently from the Euclidean GCD definition. This avoids
    // adding a second divider network to the already bounded sequential proof.
    always @* begin
        case ({a_in, b_in})
            6'b000000: expected_gcd = 3'd0;
            6'b000001: expected_gcd = 3'd1;
            6'b000010: expected_gcd = 3'd2;
            6'b000011: expected_gcd = 3'd3;
            6'b000100: expected_gcd = 3'd4;
            6'b000101: expected_gcd = 3'd5;
            6'b000110: expected_gcd = 3'd6;
            6'b000111: expected_gcd = 3'd7;
            6'b001000: expected_gcd = 3'd1;
            6'b001001: expected_gcd = 3'd1;
            6'b001010: expected_gcd = 3'd1;
            6'b001011: expected_gcd = 3'd1;
            6'b001100: expected_gcd = 3'd1;
            6'b001101: expected_gcd = 3'd1;
            6'b001110: expected_gcd = 3'd1;
            6'b001111: expected_gcd = 3'd1;
            6'b010000: expected_gcd = 3'd2;
            6'b010001: expected_gcd = 3'd1;
            6'b010010: expected_gcd = 3'd2;
            6'b010011: expected_gcd = 3'd1;
            6'b010100: expected_gcd = 3'd2;
            6'b010101: expected_gcd = 3'd1;
            6'b010110: expected_gcd = 3'd2;
            6'b010111: expected_gcd = 3'd1;
            6'b011000: expected_gcd = 3'd3;
            6'b011001: expected_gcd = 3'd1;
            6'b011010: expected_gcd = 3'd1;
            6'b011011: expected_gcd = 3'd3;
            6'b011100: expected_gcd = 3'd1;
            6'b011101: expected_gcd = 3'd1;
            6'b011110: expected_gcd = 3'd3;
            6'b011111: expected_gcd = 3'd1;
            6'b100000: expected_gcd = 3'd4;
            6'b100001: expected_gcd = 3'd1;
            6'b100010: expected_gcd = 3'd2;
            6'b100011: expected_gcd = 3'd1;
            6'b100100: expected_gcd = 3'd4;
            6'b100101: expected_gcd = 3'd1;
            6'b100110: expected_gcd = 3'd2;
            6'b100111: expected_gcd = 3'd1;
            6'b101000: expected_gcd = 3'd5;
            6'b101001: expected_gcd = 3'd1;
            6'b101010: expected_gcd = 3'd1;
            6'b101011: expected_gcd = 3'd1;
            6'b101100: expected_gcd = 3'd1;
            6'b101101: expected_gcd = 3'd5;
            6'b101110: expected_gcd = 3'd1;
            6'b101111: expected_gcd = 3'd1;
            6'b110000: expected_gcd = 3'd6;
            6'b110001: expected_gcd = 3'd1;
            6'b110010: expected_gcd = 3'd2;
            6'b110011: expected_gcd = 3'd3;
            6'b110100: expected_gcd = 3'd2;
            6'b110101: expected_gcd = 3'd1;
            6'b110110: expected_gcd = 3'd6;
            6'b110111: expected_gcd = 3'd1;
            6'b111000: expected_gcd = 3'd7;
            6'b111001: expected_gcd = 3'd1;
            6'b111010: expected_gcd = 3'd1;
            6'b111011: expected_gcd = 3'd1;
            6'b111100: expected_gcd = 3'd1;
            6'b111101: expected_gcd = 3'd1;
            6'b111110: expected_gcd = 3'd1;
            6'b111111: expected_gcd = 3'd7;
            default: expected_gcd = '0;
        endcase
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
