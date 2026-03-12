/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_judyladella_pixel_scan (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,    // Dedicated outputs
    input  wire [7:0] uio_in,    // IOs: Input path
    output wire [7:0] uio_out,   // IOs: Output path
    output wire [7:0] uio_oe,    // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,       // always 1 when the design is powered, so you can ignore it
    input  wire       clk,       // clock
    input  wire       rst_n       // reset_n - low to reset
);

  // Unused bidirectional IOs for this design
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  // Inputs
  wire start      = ui_in[0];
  wire continuous = ui_in[1];
  wire hold       = ui_in[2];

  // Clock divider (slow tick) 
  // For faster simulation, use smaller DIV_BITS (4-8).
  // For slower LED-visible behavior on real silicon, use larger (18-22).
  localparam integer DIV_BITS = 4;
  reg [DIV_BITS-1:0] div_ctr;
  wire tick = &div_ctr;

  // State and counters
  reg [2:0] row;
  reg [2:0] col;
  reg       pixel_valid;
  reg       frame_done;

  localparam [1:0] S_IDLE = 2'd0;
  localparam [1:0] S_SCAN = 2'd1;
  localparam [1:0] S_DONE = 2'd2;
  reg [1:0] state;

  // Output packing
  assign uo_out = {frame_done, pixel_valid, row, col};

  // advance when tick and not held and powered
  wire advance = tick & ~hold & ena;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      div_ctr     <= {DIV_BITS{1'b0}};
      row         <= 3'd0;
      col         <= 3'd0;
      pixel_valid <= 1'b0;
      frame_done  <= 1'b0;
      state       <= S_IDLE;
    end else begin
      div_ctr    <= div_ctr + 1'b1;
      frame_done <= 1'b0;  // only pulse in DONE

      case (state)
        S_IDLE: begin
          pixel_valid <= 1'b0;
          row <= 3'd0;
          col <= 3'd0;
          if (start) state <= S_SCAN;
        end

        S_SCAN: begin
          pixel_valid <= 1'b1;
          if (advance) begin
            if (col == 3'd7) begin
              col <= 3'd0;
              if (row == 3'd7) begin
                state <= S_DONE;
              end else begin
                row <= row + 3'd1;
              end
            end else begin
              col <= col + 3'd1;
            end
          end
        end

        S_DONE: begin
          pixel_valid <= 1'b0;
          frame_done  <= 1'b1; // 1-cycle pulse
          if (continuous) begin
            row <= 3'd0;
            col <= 3'd0;
            state <= S_SCAN;
          end else begin
            state <= S_IDLE;
          end
        end

        default: state <= S_IDLE;
      endcase
    end
  end

  // unused inputs
  wire _unused = &{uio_in, ui_in[7:3], 1'b0};

endmodule
