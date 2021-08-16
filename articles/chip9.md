!=!=! Title: CHIP-9
!=!=! Tags: Projects, Emulators
!=!=! Created: 1628955411

!=!=! Intro: Start
This project implements as CHIP-8 emulator / interpreter in Rust and use the CLI and the input and output device, allowing you to play CHIP-8 games on the command line. The emulator is written in Rust with a custom emulation core and uses the console_engine library for IO.
!=!=! Intro: End

### Overview

The CHIP-8 virtual machine is very straightforward, lacking virtual memory, allocation, or display synchronization and driving video out and sound through dedicated instructions. Following this, the design of our emulator is straightforward, with most of the implementation focused on emulating the individual opcodes.

We split the design of our emulator into four data structures:
- CPU: A structure that includes both the registers and memory, opcode implementations and a step instruction to move the program forward by one instruction.
- Registers: Include the current state of program registers, the program counter, and the stack.
- Memory: Encapsulates the 4kb of system RAM and includes helper methods to correctly encode / decode the data from / to big-endian. Also stores the current frame buffer.
- Machine: Joins all the pieces together. Has a single instance of CPU and Memory and includes a step function that moves the program forward by one instruction and keeps the CHIP-8 clocks (delay and sound) in sync.

<p style="display: flex; justify-content: center;">
  <img src="${{{img:chip9/screen1.jpg}}}" width="49%" />
  <img src="${{{img:chip9/screen4.jpg}}}" width="49%" />
</p>

<p style="display: flex; justify-content: center;">
  <img src="${{{img:chip9/screen3.jpg}}}" width="49%" />
  <img src="${{{img:chip9/screen2.jpg}}}" width="49%" />
</p>

### Instructions

CHIP-8 programs use fixed width two byte opcodes. The leading nibble in each opcode identifies the base instruction but there are 32 opcodes and only 16 possible assignments to a nibble so for some base opcodes other part of the opcode may be used to decide the final instruction. Annoyingly, this is not always the second nibble, so each of the extended instructions contains it's own op table.

To model this we maintain several different opcode tables. One for the base table, then one more for each opcode specific instruction. Instructions implementations are fetched by following the tables until we reach a base implementation.

The instructions are all stored big-endian and are generally straightforward in implementation. The exception to this is the mcall instruction which is meant to execute code in the host machines assembly. To avoid nesting machine specific emulators we do not treat this case, though it is generally unused in ROM's so it doesn't cause too many issues.

### CPU

### Memory

A CHIP-8 machine has 4kb of user addressable R/W RAM which is used for program code and data. It also has a small region of read only memory for storing sprites of the characters 0 through F. Memory is addressed through the 16-bit register I which is positioned using dedicated opcodes. There is also a 64x32 1-bit frame buffer which can only be interacted with through the clear display and draw sprite instructions.

### Display

CHIP-8 systems use a 64 by 32 black and white display. The display is one bit, and is unable to show shades of gray. Internally this is represented through a boolean frame buffer with space for 64x32 boolean values. There is no vertical synchronization or double buffering logic in CHIP-8, instead the screen can be redrawn after every frame buffer operation. This can lead to visual artifacting but generally games design around this.

### Sound

CHIP-8 can only play a sound through it's sound register. A sound while play whenever the value in the register is not zero. While the register is not zero it will tick down at a frequency of 60hz.

### Source Code

The code is open source and available on [Github](https://github.com/jawline/CHIP-9/).
