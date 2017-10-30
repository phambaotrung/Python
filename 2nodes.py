# Example of interaction with a BLE UART device using a UART service
# implementation.
# Author: Tony DiCola
import time
import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART

# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()


# Main function implements the program logic so it can run in a background
# thread.  Most platforms require the main thread to handle GUI events and other
# asyncronous events like BLE actions.  All of the threading logic is taken care
# of automatically though and you just need to provide a main function that uses
# the BLE provider.

def get_scan_devices():
    # global adapter
    adapter = ble.get_default_adapter()
    adapter.power_on()

    # initialize an empty set
    known_uarts = set()

    try:
        # Start scanning with the bluetooth adapter.
        adapter.start_scan()

        # Scan for UART devices.
        print('Searching for UART device(timeout after 5 sec)...'),

        prev_time = curr_time = time.time()
        while (curr_time - prev_time) <= 3:  # stop scanning if more than 30 seconds
            # Call UART.find_devices to get a list of any UART devices that
            # have been found.  This call will quickly return results and does
            # not wait for devices to appear.
            found = set(UART.find_devices())
            # Check for new devices that haven't been seen yet and print out
            # their name and ID (MAC address on Linux, GUID on OSX).
            new = found - known_uarts

            # add new devices to set
            known_uarts.update(new)

            # Sleep for a second and see if new devices  have appeared.
            time.sleep(1.0)

            # update the current time before the conditions ~
            curr_time = time.time()
    finally:
        # stop the bluetooth adapter when done scanning/discovery devices
        adapter.stop_scan()
    print('found!')
    # return whatever devices we found.
    return known_uarts


def connect_ble_devices():
    # global devices, uart
    connected_uarts = list()
    known_uarts = get_scan_devices()  # run def
    devices = list(known_uarts)
    isFinishedConnecting = False
    while not isFinishedConnecting:
        FoundFriendId = list()
        FoundFriendNo = 0
        print('\n/---- UART Devices ----/')
        for idx, device in enumerate(devices):
            print('{0}: {1} [{2}]'.format(idx + 1, device.name, device.id)),
            if device.name.find("Bluefruit") >= 0:
                print " === Found friend, shaking hand!"
                FoundFriendId.insert(0, idx + 1)
                # FoundFriendId.append(idx + 1)
                FoundFriendNo += 1
            else:
                print " --- not my friend!"
        # print ('CHECKPOINT1')
        print (FoundFriendNo)
        while True:
            if FoundFriendNo > 0:
                index = FoundFriendId[FoundFriendNo - 1]
                FoundFriendNo -= 1

            else:
                isFinishedConnecting = True
                break
            # try:
            #     index = int(raw_input('Input a valid index (type 0 to exit):'))
            # except ValueError:
            #     continue

            if len(devices) == 0:
                break

            if 0 < index <= len(devices):
                device = devices[index - 1]
                # print ('CHECKPOINT 2')
                print (device.name)

                # print('\nConnecting to {0} [{1}].. '.format(device.name, device.id)),
                # print ('OKAY')
                device.connect()
                print('success!')
                # print ('CHECKPOINT 3')
                connected_uarts.append(device)
                # known_uarts.remove(device)

                # devices = list(known_uarts)
                # print ('CHECKPOINT 4')
            elif index <= 0:
                isFinishedConnecting = True
                break

    # print ('CHECKPOINT5')
    return connected_uarts


def bleinit():
    global uart
    print('-----Wireless Voltage Test-----')
    print('Start searching')
    ble.clear_cached_data()

    global adapter, devices, uart
    adapter = ble.get_default_adapter()
    adapter.power_on()
    print('Using adapter: {0}'.format(adapter.name))

    # Disconnect any currently connected UART devices.  Good for cleaning up and
    # starting from a fresh state.
    print('Disconnecting any connected UART devices...'),
    UART.disconnect_devices()
    print "done!"
    # get all the connected devices
    devices = connect_ble_devices()

    print('**************************')
    print('discovering UART service'),
    while True:
        try:
            # Wait for service discovery to complete for the UART service.  Will
            # time out after 60 seconds (specify timeout_sec parameter to override).
            print('Discovering services...'),
            UART.discover(devices[0], timeout_sec=2)
            if len(devices) == 2:
                UART.discover(devices[1], timeout_sec=2)

            # Once service discovery is complete create an instance of the service
            # and start interacting with it.
            uart = list()
            uart.append(UART(devices[0]))
            if len(devices) == 2:
                uart.append(UART(devices[1]))
            break
        except:
            print "FAILED!!!"
            raise
    print "done!"



def main():
    bleinit()
    secondStage = False
    global myOffSet
    global floraOffSet1
    global floraOffSet2
    while True:

        # Write a string to the TX characteristic.
        ms = int(round(time.time() * 1000))
        uart[0].write('S' + str(ms) + '\r\n')
        uart[1].write('S' + str(ms) + '\r\n')

        print("Sent PC timestamp(" + str(ms) + ") to the Flora.")

        # Now wait up to one minute to receive data from the device.
        print('Waiting up to 60 seconds to receive data from the device...')
        count = 0
        while count != 50:

            received1 = uart[0].read(timeout_sec=1)

            while (received1 is None or not received1.endswith('#') or not received1.startswith('$')):
                if received1 is not None:
                    received1 = received1 + uart[0].read(timeout_sec=1)
                else:
                    received1 = uart[0].read(timeout_sec=1)


            received2 = uart[1].read(timeout_sec=1)

            while (received2 is None or not received2.endswith('#') or not received2.startswith('$')):
                if received2 is not None:
                    received2 = received2 + uart[1].read(timeout_sec=1)
                else:
                    received2 = uart[1].read(timeout_sec=1)



            received1 = received1.replace('#', '')
            received1 = received1.replace('$', '')
            received2 = received2.replace('#', '')
            received2 = received2.replace('$', '')



            if received1 is not None and received2 is not None:
                if received1 == 'done' and received2 == 'done': break
                print 'received from flora1 ' + received1
                print 'received from flora2 ' + received2
                change = int(received2) - int(received1)
                time.sleep(0.5)
                if change >= 0:
                    uart[0].write('R' + str(change) + '\r\n')
                    uart[1].write('R' + '0' + '\r\n')
                    print 'sent back offset:'
                    print (change)
                else:
                    uart[1].write('R' + str(change) + '\r\n')
                    uart[0].write('R' + '0' + '\r\n')
                    print 'sent back offset:'
                    print (change)

                if abs(change) <= 5:
                    myOffSet = change
                    received1 = uart[0].read(timeout_sec=1)
                    while (received1 is None or not received1.endswith('#') or not received1.startswith('$')):
                        if received1 is not None:
                            received1 = received1 + uart[0].read(timeout_sec=1)
                        else:
                            received1 = uart[0].read(timeout_sec=1)

                    time.sleep(1)

                    received2 = uart[1].read(timeout_sec=1)

                    while (received2 is None or not received2.endswith('#') or not received2.startswith('$')):
                        if received2 is not None:
                            received2 = received2 + uart[1].read(timeout_sec=1)
                        else:
                            received2 = uart[1].read(timeout_sec=1)



                    uart[0].write('C' + str(change)+ '\r\n')
                    uart[1].write('C' + str(change)+ '\r\n')
                    print 'Switching to NTP approach'
                    break

                count = 0
            else:
                # Timeout waiting for data, None is returned.
                print('Received no data!')


                count = count + 1

            print("---")
            time.sleep(1)


        while True:
            # print 'Second Stage going on'
            floraOffSet1 = 0
            floraOffSet2 = 0
            # time.sleep(0.5)
            ms = int(round(time.time() * 1000))
            uart[0].write('S' + str(ms) + '\r\n')
            uart[1].write('S' + str(ms) + '\r\n')


            # print('Waiting up to 60 seconds to receive data from the device...')
            count = 0
            while count <= 12:
                count += 1
                received1 = uart[0].read(timeout_sec=1)
                t2_0 = int(round(time.time() * 1000))
                while (received1 is None or not received1.endswith('#') or not received1.startswith('$')):
                    if received1 is not None:
                        received1 = received1 + uart[0].read(timeout_sec=1)
                    else:
                        received1 = uart[0].read(timeout_sec=1)
                        # print 'in loop 1'
                        # print 'received from uart1 ' + received1
                received1 = received1.replace('#', '')
                received1 = received1.replace('$', '')
                if received1 is not None:
                    if received1 == 'done': break
                    print('Time received data: {0}'.format(t2_0))

                    # Received data, print it out.
                    print('Data Received: {0} | {1}'.format(received1, t2_0 - int(received1)))

                    t3 = int(round(time.time() * 1000))
                    diff = t3 - t2_0

                    uart[0].write('R' + str(t3) + '|' + str(diff) + '\r\n')

                    # printout replied time
                    print('Replied on: {0} | {1}'.format(t3, diff))
                    # Trying to response back to Flora

                received2 = uart[1].read(timeout_sec=1)
                t2_1 = int(round(time.time() * 1000))
                while (received2 is None or not received2.endswith('#') or not received2.startswith('$')):
                    if received2 is not None:
                        received2 = received2 + uart[1].read(timeout_sec=1)
                    else:
                        received2 = uart[1].read(timeout_sec=1)

                received2 = received2.replace('#', '')
                received2 = received2.replace('$', '')
                if received2 is not None:
                    if received2 == 'done': break
                    print('Time received data: {0}'.format(t2_1))

                    # Received data, print it out.
                    print('Data Received: {0} | {1}'.format(received2, t2_1 - int(received2)))

                    t3 = int(round(time.time() * 1000))
                    diff = t3 - t2_1

                    uart[1].write('R' + str(t3) + '|' + str(diff) + '\r\n')

                    # printout replied time
                    print('Replied on: {0} | {1}'.format(t3, diff))
                    # Trying to response back to Flora
                print 'received data from both floras'

                if count >2:
                    floraOffSet1 += int(received1)
                    floraOffSet2 += int(received2)





                else:

                    print('Received no data!')

                    count = count + 1

                print("---")

            break
        break
    # print 'Average offset of flora 1 with PC is ' + str(floraOffSet1/10)
    # print 'Average offset of flora 2 with PC is ' + str(floraOffSet2/10)
    print 'Offset of 2 floras using NTP approach: ' + str((floraOffSet2 - floraOffSet1)/10)+'ms'
    print 'Offset of 2 floras using accelerometer: ' + str(myOffSet)+'ms'

# Initialize the BLE system.  MUST be called before other BLE calls!
ble.initialize()

# Start the mainloop to process BLE events, and run the provided function in
# a background thread.  When the provided main function stops running, returns
# an integer status code, or throws an error the program will exit.
ble.run_mainloop_with(main)
