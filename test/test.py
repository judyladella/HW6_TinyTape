# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start pixel scan controller test")

    # Use a reasonably fast clock for CI
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Check unused bidirectional IO behavior
    assert int(dut.uio_out.value) == 0, "uio_out must be 0"
    assert int(dut.uio_oe.value) == 0, "uio_oe must be 0"

    def unpack():
        """Return row, col, pixel_valid, frame_done from uo_out bitfield."""
        uo = int(dut.uo_out.value)
        col = (uo >> 0) & 0x7
        row = (uo >> 3) & 0x7
        pixel_valid = (uo >> 6) & 0x1
        frame_done = (uo >> 7) & 0x1
        return row, col, pixel_valid, frame_done

    async def wait_for_pixel_valid(timeout_cycles=20000):
        for _ in range(timeout_cycles):
            await RisingEdge(dut.clk)
            row, col, pv, fd = unpack()
            if pv == 1:
                return
        assert False, "Timed out waiting for pixel_valid to assert"

    async def wait_for_addr_change(prev_row, prev_col, timeout_cycles=200000):
        for _ in range(timeout_cycles):
            await RisingEdge(dut.clk)
            row, col, pv, fd = unpack()
            if pv == 1 and (row != prev_row or col != prev_col):
                return row, col
        assert False, "Timed out waiting for next (row,col) change"

    # Configure: continuous=0, hold=0
    # ui_in[0]=start, ui_in[1]=continuous, ui_in[2]=hold
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)

    # Pulse start
    dut.ui_in.value = 0b0000_0001
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)

    # Wait for scan to begin
    await wait_for_pixel_valid()

    # Verify first pixel
    row, col, pv, fd = unpack()
    assert pv == 1, "pixel_valid should be 1 during scan"
    assert (row, col) == (0, 0), f"Expected first pixel (0,0), got ({row},{col})"

    prev_row, prev_col = row, col

    # Check full row-major order over all 64 pixels
    for exp_row in range(8):
        for exp_col in range(8):
            if exp_row == 0 and exp_col == 0:
                continue

            new_row, new_col = await wait_for_addr_change(prev_row, prev_col)

            row, col, pv, fd = unpack()
            assert pv == 1, "pixel_valid should remain high during scan"
            assert (row, col) == (exp_row, exp_col), \
                f"Expected ({exp_row},{exp_col}), got ({row},{col})"

            prev_row, prev_col = new_row, new_col

    # After the last pixel, we expect frame_done pulse and pixel_valid to drop (IDLE) if continuous=0
    saw_frame_done = False
    for _ in range(200000):
        await RisingEdge(dut.clk)
        row, col, pv, fd = unpack()
        if fd == 1:
            saw_frame_done = True
        if saw_frame_done and pv == 0:
            break

    assert saw_frame_done, "Did not see frame_done pulse after full frame"
    dut._log.info("PASS: Pixel scan controller behavior verified")