// Experiment architecture: register the odd-operand comparison, then use
// one shared subtractor in the following cycle. The extra cycle may shorten
// the combinational feedback path; PPA must be measured, not assumed.
module gcd_binary_split #(
    parameter integer WIDTH = 32
) (
    input  logic             clk,
    input  logic             rst,
    input  logic             start,
    input  logic [WIDTH-1:0] a_in,
    input  logic [WIDTH-1:0] b_in,
    output logic [WIDTH-1:0] gcd_out,
    output logic             busy,
    output logic             done
);
    localparam integer SHIFT_WIDTH = (WIDTH < 2) ? 1 : $clog2(WIDTH + 1);
    localparam logic [1:0] ST_IDLE = 2'd0;
    localparam logic [1:0] ST_RUN = 2'd1;
    localparam logic [1:0] ST_SUBTRACT = 2'd2;

    logic [1:0] state;
    logic [WIDTH-1:0] x, y;
    logic [SHIFT_WIDTH-1:0] common_shift;
    logic x_gt_y;

    wire [WIDTH-1:0] subtract_lhs = x_gt_y ? x : y;
    wire [WIDTH-1:0] subtract_rhs = x_gt_y ? y : x;
    wire [WIDTH-1:0] subtract_result = subtract_lhs - subtract_rhs;

    assign busy = (state != ST_IDLE);

    always_ff @(posedge clk) begin
        if (rst) begin
            state        <= ST_IDLE;
            x            <= '0;
            y            <= '0;
            common_shift <= '0;
            x_gt_y       <= 1'b0;
            gcd_out      <= '0;
            done         <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                ST_IDLE: begin
                    if (start) begin
                        if ((a_in == '0) && (b_in == '0)) begin
                            gcd_out <= '0;
                            done    <= 1'b1;
                        end else if (a_in == '0) begin
                            gcd_out <= b_in;
                            done    <= 1'b1;
                        end else if (b_in == '0) begin
                            gcd_out <= a_in;
                            done    <= 1'b1;
                        end else begin
                            x            <= a_in;
                            y            <= b_in;
                            common_shift <= '0;
                            x_gt_y       <= 1'b0;
                            state        <= ST_RUN;
                        end
                    end
                end
                ST_RUN: begin
                    if (x == y) begin
                        gcd_out <= x << common_shift;
                        done    <= 1'b1;
                        state   <= ST_IDLE;
                    end else if (x == '0) begin
                        gcd_out <= y << common_shift;
                        done    <= 1'b1;
                        state   <= ST_IDLE;
                    end else if (y == '0) begin
                        gcd_out <= x << common_shift;
                        done    <= 1'b1;
                        state   <= ST_IDLE;
                    end else if (!x[0] && !y[0]) begin
                        x            <= x >> 1;
                        y            <= y >> 1;
                        common_shift <= common_shift + 1'b1;
                    end else if (!x[0]) begin
                        x <= x >> 1;
                    end else if (!y[0]) begin
                        y <= y >> 1;
                    end else begin
                        x_gt_y <= (x > y);
                        state  <= ST_SUBTRACT;
                    end
                end
                ST_SUBTRACT: begin
                    if (x_gt_y) x <= subtract_result;
                    else        y <= subtract_result;
                    state <= ST_RUN;
                end
                default: state <= ST_IDLE;
            endcase
        end
    end
endmodule
