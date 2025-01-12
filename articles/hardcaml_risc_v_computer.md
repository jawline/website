!=!=! Uuid: 2820730e-9960-40f7-a240-3187f805131b
!=!=! Title: Building a risc-v computer with Hardcaml (Part 1: Memory)
!=!=! Created: 1736615772
!=!=! Tags: Work, Research, Projects

!=!=! Intro: Start
In this series we will design a minimal risc-v computer for an FPGA. This
computer will have memory and IO controllers in addition to the CPU core. As a
final step we will also add support for a simple frame buffer based video out.
!=!=! Intro: End

This article will be split into the following parts:
- Part 1: Memory
- Part 2: Processor
- Part 3: I/O
- Part 4: Video

## Motivation

TODO: Motivate a computer

## Overview

It is easy to assume that the most complicated component of such a system will
be the CPU itself, but in practice for such a simple architecture the bulk of
our systems complexity will be spent building a general memory controller to
arbitrate over our system memory and a DMA architecture that allows us to
communicate with our new computer. Such infrastructure is essential, as without
it we would not be able to program our computer or receive its output.

To begin, we design out an interface that components will use to perform memory
requests. We then construct a memory controller, a component that receives and
arbitrates all memory requests from the various different components in our
system and signals back to those components with the result.

For our underlying memory, we will use BRAM (Block RAM). These are small blocks
of RAM that typically exist directly on an FPGA. These RAMs can be combined to
create one larger logical RAM. We use these as they will exist on most FPGAs
and are typically easy to use, however our memory controller design is pretty
general and should extend to other memory (e.g., DDR) without any change to the
interface.

<img src="/images/memory_architecture.png" style="margin: 10px;" height="400px;" />

Once finished, our systems memory architecture will look like the figure, with
the CPU, IO, and video controllers each having a line to make read requests
from and the CPU and IO controllers having a line to make write requests to. In
reality, the CPU will actually have several read lines so that the fetcher and
executors can work independently, but this is an implementation detail.

## Implementation
