# USB and wireless transports

## USB

Require Developer options + USB debugging, unlocked device, data-capable cable/port, host USB visibility/permissions, and user approval of the workstation RSA fingerprint. Android 4.2.2+ protects adb with device-side authorization. Windows may require the OEM USB driver; Linux may require correct udev rules/group access; macOS normally needs no driver.

States from `adb devices -l`: `device` (adbd connected, OS may still boot), `offline`, `unauthorized` (commonly displayed though guide’s abbreviated list omits it), recovery/sideload/bootloader transports. Verify boot separately.

## Secure wireless debugging

Android 11+ phone/tablet and Android 13+ TV/Wear support Wireless debugging pairing. Host/device must share an allowed network.
1. enable Wireless debugging
2. select pairing by code
3. run `adb pair IP:PAIR_PORT`
4. enter code interactively
5. allow mDNS auto-connect or run `adb connect IP:CONNECT_PORT`

Pairing and connection endpoints differ. Pair once; trust persists until forgotten/revoked. Never put pairing code in shell history/logs. Trusted-network auto-connect/Wi-Fi 2.0 needs Android 17 + adb 37 and matching service version.

Inspect `adb server-status`, `adb mdns check`, `adb mdns services`, or `adb mdns track-services --proto-text`. Check same subnet, AP/client isolation, VPN, firewall, multicast, device sleep/network change, and Wireless debugging toggle.

## Legacy TCP

Android 10/lower requires initial USB: `adb tcpip PORT`, disconnect USB, `adb connect IP:PORT`. This exposes legacy TCP transport; use only isolated trusted networks, return via `adb usb`, disconnect, and disable debugging afterward. Do not bind host adb server to all interfaces (`adb -a`) without an explicit secured architecture.
