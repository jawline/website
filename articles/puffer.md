!=!=! Uuid: deada886-3b59-4828-a2b4-500604c0b4f6
!=!=! Title: Puffer: Privacy Protection & Ad-blocking for Android
!=!=! Tags: Projects, Privacy
!=!=! Created: 1629123828

![Puffer](${{{img:puffer.png}}} =x300)

!=!=! Intro: Start
Puffer is a novel whole system privacy protector & ad-blocker for Android that outperforms existing DNS based solutions through inspection of Server Name Indication (SNI) records during initialization of TLS connections. Our solution cannot be circumvented with custom DNS resolvers or other common circumvention approaches because we inspect connections at the packet level. As such, our approach still works out of the box with browsers that use custom DNS approaches like Firefox. It also works to stop advertising in apps from circumventing ad-blockers.
!=!=! Intro: End

<p style="display: flex; justify-content: center;">
  <img src="/images/puffer1.png" style="margin: 10px;" height="400px;" />
  <img src="/images/puffer2.png" style="margin: 10px;" height="400px" />
</p>

For Android devices, the best option for whole system spyware protection and ad-blocking has traditionally been DNS based. These programs function by redirecting DNS requests made by the device to a custom on-device DNS resolver which will return either no record or broken records for websites that should be blocked. This strategy is effective on unsuspecting websites, but can be easily avoided by using a custom DNS resolver. For example, Firefox intends to ignore the system DNS resolver by default to alley privacy concerns. Since these blockers are so easy to circumvent, many other apps will include custom resolvers to ensure that spyware and ads continue to function.

SNI is an extension to TLS which allows for CDNs and load balancers to forward HTTP requests to the correct application servers without decrypting the HTTP request contents. SNI functions by making the originating client (your browser or app) include a small plaintext SNI record with routing information during the TLS handshake. A receiving server that doesn't have the keys to this message can compare the SNI record to a list of known locations and route accordingly. In the case of HTTP requests, the domain name that you would like to connect to is included in the SNI record. While this has some privacy drawbacks because intermediate parties on the internet can see what domains you intend for your encrypted messages to reach, it is straightforward and does not require an additional source of truth for key verification. While alternate solutions exist, they generally require complex changes to website deployment and are currently not widely used.

We leverage the existence of these SNI headers to perform connection level blocking of known privacy violating or advertising domains on your device without ever decrypting the HTTP requests. Traditionally, packet filter based ad-blocking has been difficult on Android when disconnected from a VPN because the OS provides no service to intercept, inspect, and then selectively forward traffic. This makes applications such as packet level firewalls and traffic monitors difficult to write for Android, but is a necessity to implement an SNI blocker. To solve this problem we create a new userspace IP stack for Android which leverages the VPN service to capture inbound packets and uses standard OS facilities to create connections to send onward data. This is necessary because while a VPN service can capture outbound packets, there is no facility to reroute the packets we want to keep back out using the system network stack. To implement this we needed to create a userspace TCP/IP and UDP/IP implementation, as well as a userspace NAT to keep track of active connections. Any packets that the device wants to send come to the network stack as raw IP packets. If we want to forward the packet to the internet we will open a corresponding OS network socket to the address indicated in the IP header and forward the message. When data is received on one of the opened OS sockets we do the same in reverse, crafting an IP and TCP or UDP header for the received data and then writing it to the VPN socket.

With this in place we implement ad-blocking by adding a firewall rule that blocks TLS packets with an SNI extension that contains a blocked domain.

Puffer does not collect any metrics from the device and is currently available entirely for free, without advertisements, on [Google Play](https://play.google.com/store/apps/details?id=com.parsed.securitywall). The code is currently not open source but if you think you have an interesting use-case for the technology feel free to reach out to me at [blake@parsed.uk](mailto:blake@parsed.uk) for potential licensing.
