module gcd_oracle_3bit (
    input wire [2:0] a,
    input wire [2:0] b,
    output reg [2:0] expected_gcd
);
    // Exhaustive 64-entry truth table generated independently from Euclid's algorithm.
    always @* begin
        case ({a, b})
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
            default: expected_gcd = 3'd0;
        endcase
    end
endmodule
