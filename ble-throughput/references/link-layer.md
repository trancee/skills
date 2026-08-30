# PHY, DLE, events, and RF

Raw rates are modulation rates, not application throughput: LE 1M = 1 Mbit/s, LE 2M = 2 Mbit/s, LE Coded S=2/S=8 trade speed for robustness/range. LE 2M is optional and may differ by direction; confirm the PHY update result.

DLE raises the LL data payload ceiling from 27 to 251 octets. Both peers negotiate TX/RX octets and times; controller/host ACL buffers must hold the configured sizes/counts. Confirm full packets on air—compile-time limits alone are not proof.

A connection interval starts opportunities; event duration and stack/controller packet/buffer limits determine how much air time is used. The central chooses effective parameters. A longer interval can preserve streaming throughput if events stay open and supplied, while increasing latency; a shorter interval may only expose the same packet cap more often.

Legacy intervals start at 7.5 ms. Core 6.2 SCI can negotiate 375 us only with both controller and host support and new connection-rate procedures. Mobile framework exposure/support cannot be inferred from Core version.

Peripheral latency/subrating saves power by skipping opportunities. Its directional impact depends on who has data and continuation behavior. Measure rather than applying zero universally.

LE 2M shortens packets/radio-on time but has less link margin. Under interference/range, retries or early event termination can make 1M faster. Coded PHY is a reliability/range choice. Compare under controlled RSSI/interference and real coexistence.

Control procedures such as encryption, PHY, data length, and connection updates may serialize. Drive them through a connection state machine, wait for completion callbacks/events, and begin measurement only after effective values settle.
