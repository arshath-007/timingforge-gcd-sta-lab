// Behavioral model for the Nangate45 DFF_X1 cell used by the mapped GCD netlists.
// Pin polarity and edge behavior match the Liberty ff(IQ, IQN) definition:
// Q=IQ, QN=IQN, clocked_on=CK, next_state=D.
module DFF_X1 (
    input  wire CK,
    input  wire D,
    output wire Q,
    output wire QN
);
    reg IQ;
    always @(posedge CK)
        IQ <= D;
    assign Q = IQ;
    assign QN = ~IQ;
endmodule
