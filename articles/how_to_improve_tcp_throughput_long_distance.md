!=!=! Title: How to speed up long-distance HTTP file downloads by 6x
!=!=! Created: 10-12-2020
!=!=! Tags: Projects 

!=!=! Intro: Start
The vast majority of HTTP communications use the TCP protocol to transfer data. TCP connections deliver data in-order and without message loss through the use of retransmits and message buffers. Since buffers need to store all sent messages before they are acknowledged, the maximum achievable throughput of a TCP connection is calculatable by a function of buffer size and latency. In long distance communications, this maximum throughput is often lower than the line speed, slowing down the connection on a line that could support faster communications. In this article we explore what impact these buffers have on TCP connection throughput in Linux for HTTP file downloads, demonstrating performance improvements of up to 6x over Ubuntu defaults on a connection with a 200ms ping.
!=!=! Intro: End

# TLDR; 

```
sysctl -w net.core.wmem_max=2147483647
sysctl -w net.core.rmem_max=2147483647
sysctl -w net.core.optmem_max=50331648
sysctl -w net.ipv4.tcp_mem="2097152 2097152 2097152"
sysctl -w net.ipv4.tcp_rmem="1024000 8738000 2147483647"
sysctl -w net.ipv4.tcp_wmem="1024000 8738000 2147483647"
```
Running the above script on both the client and server will increase download throughput on long distance at the cost of increased memory usage (up to 8GB of memory allocated across all TCP streams) on both the server and client.

# Explained

The TCP protocol guarentees lossless in-order communication through the use of receive and transmit buffers, memory dedicated to holding the contents of messages which have not finished processing yet. The receive buffers store fragments of messages received out of order until all preceeding data is accounted for, while transmit buffers store messages that have been sent but are not yet acknowledged, in case they need to be retransmitted. Typically these buffers are allocated a finite amount of memory per-stream by an operating system, and exhaustion of these buffers leads to stalled connections and overall lower throughput.

Latency, the time it takes for a message transmitted to be received, is particularly good at triggering the exhaustion of TCP connection buffers. Every message sent by a TCP connection must be acknowledged by the receiving side before it can be removed from the sender's transmit buffer, which means that even in ideal conditions a single round trip must take place before a slot in the transmit buffer can be freed. If the buffer is exhausted then the sender will stall, since no new messages can be added to the transmit buffer. As such, when sending lots of data long-distance, the maximum achievable throughput is:
```
buffer size in bytes * (1 / latency in seconds)
```
This bottleneck, plus the fairly opaque relationship between buffer size, latency, and overall connection throughput, can often make users believe that their internet connection is slow, when really they have just failed to allocate enough memory to take full advantage of the bandwidth they have available.

NOTE: Arrangement of TCP windows is a component of the TCP protocol we will gloss over today. TCP connections communicate their buffer sizes as windows, so that the other end of a connection does not overwhelm them with too much data. On Linux, the window size communicated is decided by the memory allowed to be allocated to a single TCP connection.

# Experiment

In this experiment we demonstrate the impact that TCP buffer sizes have on long-distance TCP connection throughput by configuring buffer sizes on a Linux (Ubuntu) server and client. To do this we download a randomly generated file over a server hosted in Germany from a client in Hong Kong (~200ms ping). Linux allows users to change the minimum, maximum, and default amount of memory allocated to each TCP stream. Most distributions set low limits by default in order to preserve system resources. In our experiment we show that the impact of increasing these values on both the client and server can be quite dramatic, demonstrating up to a 6x increase in HTTP download speed.

## Low Defaults

This work was motivated after observing that the Debian and Ubuntu default buffer sizes seemed to be set too low. At time of writing the TCP sysctl settings on my Regolith Linux (Ubuntu derived distribution) were set to:
```
net.ipv4.tcp_rmem = 4096 131072 6291456
net.ipv4.tcp_wmem = 4096 16384 4194304
```
In simple terms, this allows for a 6MB receive buffer and a 4MB send buffer. Thus, by the formula above our total achievable throughput is:
```
600000 * (1/0.2) = ~3MB/s = ~50Mbps
```
This total achievable throughput is a far cry from the potential of our gigabit network, which should enable transfers at nearly 125MB/s.

## Methodology

We configure two Linux machines (Ubuntu Server), one acting as a client and one acting as a webserver. The server machine has the maximum buffer sizes enabled and a large file to download hosted via NGINX. Both our client and server have 1Gbps internet links, with the client located in Hong Kong and the server in Germany.

For each buffer size we set the client's transmit and receive TCP buffer limit and default to the specified size, but we do not change other TCP settings. For these tests we use the default TCP congestion profile on Ubuntu (cubic) and have default settings for TCP slow start.

To test bandwidth we set the large file downloading with a time limit of ten minutes. As the file downloads we the average throughput. To automate this test we use the following scripts:
```
# run_tests
while read p; do
  echo "# Starting test with $p"
  ./configure_settings "${p}"

  echo "# Sleeping"
  sleep 240

  echo "# Going"
  timeout 10m curl http://dev.parsed.uk/file.data --output /dev/null

done < test.txt 
```
This script sequentially executes the same test with different test configurations loaded from test.txt.

```
# prepare for test
sysctl -w net.core.wmem_default=2147483647
sysctl -w net.core.rmem_default=2147483647
sysctl -w net.core.wmem_max=2147483647
sysctl -w net.core.rmem_max=2147483647
sysctl -w net.core.optmem_max=50331648
sysctl -w net.ipv4.tcp_mem="2097152 2097152 2097152"
sysctl -w net.ipv4.tcp_rmem="$1"
sysctl -w net.ipv4.tcp_wmem="$1"
sysctl -w net.ipv4.route.flush=1
```
This script sets the TCP parameters for the test. The scripts are available on Github [here](https://github.com/jawline/tcp-test-configuration). We allowed a four minute period between setting sysctl settings and beginning the test to allow for the TCP settings to properly apply.

## Results & Conclusions

![Results Graph](${{{img:tcp_graph.png:original}}})

From our results we see that the TCP buffer sizes have a significant impact on throughput long distance. The maximum throughput observed during testing (21MB/s) was over 6x faster than the throughput for the client with a default configuration (~3-4MB/s). We observe that increases in buffer size correlate with increased in throughput until we reach 64MB TCP buffers. In our tests we see throughput peak at 21MB/s, and see no further gain in increasing buffer sizes beyond this. This is likely a limitation of one of the two servers, or the network that links them together. If our testing was not limited by other factors, we should observe further increases in performance was we increase TCP buffer sizes beyond that. Additionally, note that our testing is not rigerous, we performed a single test at each TCP memory increments and do not control for external factors such as network fluctuations or peak time load at the datacenter. Regardless, the limited testing methodology is still sufficient to show the clear trend of increasing throughput with TCP buffer sizes.

While unbounding the maximum buffer sizes is probably not ideal for most configurations, we suggest increasing buffer sizes to allow for 64-128MB per TCP stream on systems where the memory is available. 
