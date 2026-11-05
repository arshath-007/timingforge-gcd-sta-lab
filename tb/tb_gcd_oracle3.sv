`timescale 1ns/1ps
module tb_gcd_oracle3;
    reg [2:0] a = 0;
    reg [2:0] b = 0;
    wire [2:0] expected_gcd;
    integer ai, bi;

    gcd_oracle_3bit u_oracle (.a(a), .b(b), .expected_gcd(expected_gcd));

    function automatic [2:0] gcd_ref(input [2:0] x, input [2:0] y);
        reg [2:0] remainder;
        begin
            while (y != 0) begin
                remainder = x % y;
                x = y;
                y = remainder;
            end
            gcd_ref = x;
        end
    endfunction

    initial begin
        for (ai = 0; ai < 8; ai = ai + 1) begin
            for (bi = 0; bi < 8; bi = bi + 1) begin
                a = ai[2:0];
                b = bi[2:0];
                #1;
                if (expected_gcd !== gcd_ref(a, b))
                    $fatal(1, "WIDTH=3 oracle mismatch a=%0d b=%0d expected=%0d actual=%0d",
                           a, b, gcd_ref(a, b), expected_gcd);
            end
        end
        $display("PASS: exhaustive 3-bit GCD oracle table verified for all 64 operand pairs");
        $finish;
    end
endmodule
