!=!=! Uuid: da0f8493-89c6-443d-889c-868d7b610f3c
!=!=! Title: Integrating io_uring with Async to speed up file IO in OCaml
!=!=! Tags: Projects, OCaml
!=!=! Created: 1629555796

### Introduction

!=!=! Intro: Start
In this article we integrate io_uring into the OCaml Async library. We find that the biggest advantage in OCaml integration is the removal of costly thread pooling and demonstrate an 85% improvement in performance of an IO heavy workload. We provide an open source prototype for further exploration.
!=!=! Intro: End

The Async library is a popular choice for OCaml programs that need to perform two IO operations without blocking. The library allows a single threaded program to continue processing tasks while waiting for a file of socket an lets single threaded programs execute many tasks concurrently. The library provides a monadic interface to represent asynchronous actions along with a set of methods to create and schedule new deferred operations.

Under the hood Async uses either poll or epoll for non-blocking operatIOns like networking but falls back to thread pools for operations that do not have non-blocking APIs, such as reading and writing to a file. The use of thread pools comes with significant performance overhead because the OCaml garbage collector requires a global lock on program execution which prevents to pieces of OCaml code from executing in parallel. As such, the existence of other threads causes lock contention which can cause the program to spend less time doing useful work and thus increasing overall program runtime. In addition, the use of a random thread in a pool to service each IO operation can lea to inefficient scheduling.

Previously, the compromise was necessary because there was no facility for general asynchronous IO on Linux but the addition of io_uring to the kernel provides an opportunity to remove this overhead. io_uring is the first API for Linux that includes support for truly asynchronous file IO. Unlike previous attempts, io_uring uses the same system calls as the existing blocking behaviours but provides a way to asynchronously wait for operations to complete using a ring buffer. io_uring functions by creating submissions and competitions rings which share memory with the kernel. Instead of interrupting to trigger a system call, a program will write details of the system call it want's to execute to the submissions ring and then issue a submit system call that alerts the kernel to a change but returns immediately. The kernel then processes the system call as it would normally, but when it is finished it writes the result to the completion ring instead of returning the details to the caller. This allows for any supported system call to be executed asynchronously while still behaving as if it is blocking. Critically, this allows us to model file reads and writes without multiple threads, but it also allows us to shedule multiple IO operations using a single system call which can also improve performance in networked applications that service lots of small messages.

### Architecture

Async is split into two components which are partitioned as OCaml libraries. These components are:
1. Async kernel: The core abstractions and the foundation for scheduling. All of the components you need to build an Async library without any of the operating system specific parts.
2. Async unix: A combination of the platform specific scheduling logic and implementations of platform specific IO such as reader and writer.
Annoyingly, this partition makes it difficult to cleanly integrate Async into the existing code while staying consistent with the current interface because lots of the re-usable components of Async are meshed together with operating system specific logic. As such, we have three reasonable approaches when modifying this design to include support for io_uring:
1. Rework Async_unix to use an io_uring backend exclusively.
2. Create a small io_uring instance inside Async_unix and gradually transition methods to the newer backend.
3. Replace Async_unix with a new library Async_uring and reimplement all utilities.
In this article we explore option 3), a complete replacement of Async_unix and we build a prototype that validates our design. This prototype includes a new io_uring backed scheduler, as well as implementations of reader and writer and some utilities open files and TCP streams. In practice, it would probably be more pragmatic to gradually refactor Async_unix to support either backend in a backward compatible manner but the scope of the work is much wider.

#### Scheduler

The scheduler plays a key role in every async program. It is a globally accessible singleton created at startup that keeps track of all scheduled IO, uncompleted work, and timers. This component drives the event loop forward after program initialization by watching for IO completion and filling the corresponding `Deferred.t` structures with values so execution can continue. It is also responsible for executing any scheduled work that is no longer blocked waiting for IO or a timer. The general work loop of a scheduler instance is:
1. Check for completed IO or timer events and fill in `Deferred.t` values.
2. Execute any functions which were waiting for the filled in values (scheduled by `bind` on a `Deferred.t`).
3. Wait for the next IO event to complete
In the case of 3) the wait is usually achieved through a syscall that tells the operating system to sleep the program until one of the awaited events occurs, reducing CPU usage for IO bound programs.

To create our io_uring backed scheduler we can reuse most of the default scheduling behaviour inside Async_kernel, but we need to implement steps 1) and 3) ourselves. To do this we create a new uring during scheduler creation and store it in the scheduler record. After the scheduled is created the program is initialized and some events are scheduled before entering the event loop. When an IO event is scheduled we will construct a callback function that takes in the result code and fill the appropriate `Ivar`, a structure that is paired with a `Deferred.t` and used to fill in it's value. To implement 1) we will iterate the list of completions on the io_uring and execute the callback function with the result code of the completion. After that we will yield to the default behaviour for 2), which will execute any methods bound to `Deferred.t` values that have had their corresponding `Ivar.t` filled by step 1). The execution of these callback may schedule more IO events. Finally, we will call the io_uring method `submit_and_wait` which submits any waiting events to the kernel and then yields the program until at least one of the scheduled events have completed. To implement 1) we will iterate the list of completions on the io_uring and execute the callback function with the result code of the completion. After that we will yield to the default behaviour for 2), which will execute any methods bound to `Deferred.t` values that have had their corresponding `Ivar.t` filled by step 1). The execution of these callback may schedule more IO events. Finally, we will call the io_uring method `submit_and_wait` which submits any waiting events to the kernel and then yields the program until at least one of the scheduled events have completed. The cycle is then repeated until there are no more scheduled events.

#### Reader / Writer

The reader and writer structures provide abstractions for IO and are responsible for scheduling system calls to the ring as well as creating `Deferred.t` values. In Async_unix the reader and writer implement buffered IO and are responsible for scheduling operations to the thread pool or an epoll backend upon request as well as keeping track of available data. In cases that require use of the thread pool performance is greatly reduced because OCaml programs cannot execute two segments of OCaml code at the same time, though code in depended C libraries may occur in parallel with appropriate safeguards.

In our prototype we only provide methods to read bytes, open files, open TCP connections or start a TCP server. These methods function by creating a new `Ivar.t` and `Deferred.t` pair to hold the result of the operation and then constructing the callback method to be called by the scheduler once the event is completed. This callback converts the operating system return code into an OCaml type, abstracting raw `errno`. Since these callbacks are scheduled to a ring and do not require a thread pool there is much lower scheduling overhead than Async_unix.

### Results

To evaluate our prototype we test a file IO and a TCP workload. We benchmark our prototype against an equivalent Async_unix implementation using in two micro benchmarks. The first benchmark executes a checksum of a file while the second benchmark measures checksumming of data from a TCP connection.

#### Checksumming benchmark

In both the file and TCP benchmark we use the following code to simulate a mixed CPU and IO workload. The program reads data from a reader and then adds the value of each byte read to a rolling sum of bytes. This mixed workload acts as a reasonably representative example of a high load scenario for a IO bound program.

```
let rec crc accum data idx size =
  if idx = size
  then accum
  else crc (accum + Char.to_int (Bytes.unsafe_get data idx)) data (idx + 1) size
;;

let count filepath =
  let block_size = 1024 * 32 in
  let%bind reader = Reader.open_file ~buf_len:block_size filepath in
  let count = ref 0 in
  let crc_accum = ref 0 in
  let read_buffer = Bytes.create block_size in
  let rec read_loop () =
    let%bind data = Reader.read reader read_buffer in
    match data with
    | `Eof ->
      print_s [%message ~crc:(!crc_accum : int)];
      return ()
    | `Error ->
      return ()
    | `Ok bytes_count ->
      crc_accum := crc !crc_accum read_buffer 0 bytes_count;
      count := !count + bytes_count;
      read_loop ()
  in
  read_loop ()
;;
```

#### Experimental Setup

We perform all of our experiments on a machine with a 11th Gen Intel(R) Core(TM) i5-1130G7 @ 1.10GHz CPU, 16GB of RAM and an NVMe SSD drive. All wall clock times and context switches are measured by `/usr/bin/time`, so there is a relatively high margin of error (a few hundred milliseconds).

#### Checksumming a file

In file IO we see a significant performance difference between Async_unix and our io_uring prototype. The mean performance improvement is 53%, meaning that our prototype performs roughly twice as fast in workloads that contain a lot of file IO. Looking at our first figure, we see that this trend is consistent across all file sizes but the relative performance difference increases with larger files.

![Results Graph](${{{img:io_uring/file_result.png}}})

Our second figure details the relative percentage difference in performance across our experiment. Here we see that the io_uring prototype tends to finish execution just 43% of the time that it takes for the Async version to finish. It appears that this difference gets more pronounced as files near the 2GB mark, but we see an overall reduction in runtimes at around the same time so it is possible that this observation is an unanticipated side-effect of file-system caching.

![Results Graph](${{{img:io_uring/file_result_relative.png}}})

Our final figure details the number of context switches each application performed while processing it's file. Here we can see that the async version of our program spends a significant amount of it's time scheduling or yielding to the operating system, which will incur heavy overhead.

![Results Graph](${{{img:io_uring/file_result_context_switches.png}}})

#### Checksumming a TCP connection

In our TCP experiment we see a much less significant change in performance. While there does seem to be a small improvement in performance at large file sizes the overall performance change is negligable, with Async_unix performing 2% better on average across all tests..

![Results Graph](${{{img:io_uring/tcp_result.png}}})

Looking at the second figure, we see that from the relative change it appears as if the io_uring version is slightly slower overall than Asyn_unix. While this is not entirely outside the margin of measurement error for my experimental setup, it is a consistent trend across all file sizes.

![Results Graph](${{{img:io_uring/tcp_result_relative.png}}})

We attribute the lack of performance improvement to two factors. 1) Async_unix can use an epoll based backend for network IO. The epoll backend is non-blocking, so it doesn't require threadpooling, and has a very performant implementation. 2) The Async_unix reader / writer classes are mature and have various performance improvements such as buffering that are missing in my prototype. Unfortunately our experimental netcat setup prevented us from measuring the number of context switches each version performed during it's runtime but given the epoll backend is non-blocking we expect it to be consistent with the io_uring prototype. While in principle io_uring should bring some speedups to networked programs due to a reduction in the number of expensive system calls, this effect is unlikely to be pronounced when writes are large (>32kb). It is possible that our benchmark would show more compelling results in UDP workloads, where write sizes are typically limited to 1500 bytes.

#### Conclusion

We conclude that io_uring provides a compelling mechanism to avoid thread pooling and the corresponding global locking in Aync programs that interact with files. We show that an io_uring based prototype with limited optimization consistently outperforms the existing Async implementation. We attribute this dramatic improvement in performance to the reduction in context switching and lock contention on the OCaml global lock.

We were unable to demonstrate any performance improvement in networked workloads, and we generally conclude that any improvement is likely to be much less pronounced because the existing epoll backend is already performant. We believe there may be some gain in networked applications that send large numbers of small packets, but did not benchmark that workload.

### Source Code

A prototype version of Async with io_uring support is available on [Github](https://github.com/jawline/ocamlIoUringAsyncBackend).

The OCaml wrapper for io_uring I used to implement the prototype is available [here](https://github.com/mt-caret/io_uring).
