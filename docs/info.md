## How it works

This project implements a digital readout controller for an 8×8 pixel array, similar to the row/column scanning logic used in CMOS image sensors.

The controller sequentially scans all pixels in row-major order using two counters:

- A **row counter** (3 bits) selects rows 0–7
- A **column counter** (3 bits) selects columns 0–7

The scan sequence is:

(0,0) → (0,1) → ... → (0,7)  
(1,0) → (1,1) → ... → (1,7)  
.
.
.
(7,0) → ... → (7,7)

During scanning, the signal **pixel_valid** is asserted to indicate that the row and column outputs represent a valid pixel location.

After the final pixel (7,7) is reached, the controller raises **frame_done** for one clock cycle to indicate that the entire frame has been scanned.

A small clock divider slows down the scan so the behavior can be observed in simulation.

Input control signals:

- `ui_in[0]` – start scan
- `ui_in[1]` – continuous mode (automatically restart scanning)
- `ui_in[2]` – hold (pause scanning)

Output signals:

- `uo_out[2:0]` – column address
- `uo_out[5:3]` – row address
- `uo_out[6]` – pixel_valid
- `uo_out[7]` – frame_done

This architecture mimics the digital control logic used in CMOS image sensors to sequentially read pixel values from an array.

## How to test

The project is tested using a cocotb testbench.

The test performs the following steps:

1. Reset the design.
2. Set the start input (`ui_in[0]`) to begin scanning.
3. Wait for `pixel_valid` to assert.
4. Verify that the controller outputs pixel addresses in the correct row-major order:

(0,0), (0,1), ..., (0,7),  
(1,0), ..., (7,7)

5. Confirm that `frame_done` is asserted after the last pixel.

The testbench automatically checks these conditions and reports success if the scan sequence is correct.

## External hardware

No external hardware is required.

The design is purely digital and can be simulated using the provided cocotb testbench.

In a real system, the row and column outputs would be connected to a pixel array or readout circuitry in an image sensor system.