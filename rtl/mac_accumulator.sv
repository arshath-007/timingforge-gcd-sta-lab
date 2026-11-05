// Signed multiply-accumulate block for the TimingForge extension benchmark.
// ACC_WIDTH must be at least 2*DATA_WIDTH.
module mac_accumulator #(
    parameter integer DATA_WIDTH = 8,
    parameter integer ACC_WIDTH = 24
) (
    input  logic                         clk,
    input  logic                         rst,
    input  logic                         clear,
    input  logic                         enable,
    input  logic signed [DATA_WIDTH-1:0] a,
    input  logic signed [DATA_WIDTH-1:0] b,
    output logic signed [ACC_WIDTH-1:0]  acc
);
    logic signed [(2*DATA_WIDTH)-1:0] product;
    logic signed [ACC_WIDTH-1:0] product_extended;

    assign product = $signed(a) * $signed(b);
    assign product_extended = {{(ACC_WIDTH-(2*DATA_WIDTH)){product[(2*DATA_WIDTH)-1]}}, product};

    always_ff @(posedge clk) begin
        if (rst)       acc <= '0;
        else if (clear) acc <= '0;
        else if (enable) acc <= acc + product_extended;
    end
endmodule
