// Interface contract:
// - rst is synchronous, active high.
// - start is accepted only in ST_IDLE; requests while busy are ignored.
// - done is a one-cycle pulse. Zero-input requests complete on the acceptance edge.
// - gcd_out retains the most recently completed result until the next completion or reset.
// - busy is high only while an iterative operation is in progress.
// Requests with either input zero complete on the accepted clock edge; busy does not assert for them.
// The same contract applies to gcd_binary_split.
// TimingForge baseline: compare/decision/subtract occur in one RUN cycle.
// Do not assume this architecture is faster or smaller; measure it.
module gcd_binary_combined #(
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
    localparam logic ST_IDLE = 1'b0;
    localparam logic ST_RUN  = 1'b1;

    logic state;
    logic [WIDTH-1:0] x, y;
    logic [SHIFT_WIDTH-1:0] common_shift;

    assign busy = (state != ST_IDLE);

    always_ff @(posedge clk) begin
        if (rst) begin
            state        <= ST_IDLE;
            x            <= '0;
            y            <= '0;
            common_shift <= '0;
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
                    end else if (x > y) begin
                        x <= x - y;
                    end else begin
                        y <= y - x;
                    end
                end
                default: state <= ST_IDLE;
            endcase
        end
    end
endmodule
