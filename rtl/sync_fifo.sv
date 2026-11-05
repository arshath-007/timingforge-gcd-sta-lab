// Parameterized synchronous FIFO for the TimingForge extension benchmark.
// DEPTH must be a power of two. Read data is asynchronous from the current head.
module sync_fifo #(
    parameter integer WIDTH = 8,
    parameter integer DEPTH = 4,
    parameter integer PTR_WIDTH = (DEPTH < 2) ? 1 : $clog2(DEPTH),
    parameter integer COUNT_WIDTH = $clog2(DEPTH + 1)
) (
    input  logic                  clk,
    input  logic                  rst,
    input  logic                  wr_en,
    input  logic                  rd_en,
    input  logic [WIDTH-1:0]      din,
    output logic [WIDTH-1:0]      dout,
    output logic                  full,
    output logic                  empty,
    output logic [COUNT_WIDTH-1:0] count
);
    logic [WIDTH-1:0] mem [0:DEPTH-1];
    logic [PTR_WIDTH-1:0] wr_ptr, rd_ptr;

    assign full  = (count == DEPTH);
    assign empty = (count == 0);
    assign dout  = mem[rd_ptr];

    always_ff @(posedge clk) begin
        if (rst) begin
            wr_ptr <= '0;
            rd_ptr <= '0;
            count  <= '0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr] <= din;
                wr_ptr <= (wr_ptr == DEPTH-1) ? '0 : wr_ptr + 1'b1;
            end
            if (rd_en && !empty) begin
                rd_ptr <= (rd_ptr == DEPTH-1) ? '0 : rd_ptr + 1'b1;
            end
            case ({wr_en && !full, rd_en && !empty})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end
endmodule
