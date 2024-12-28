import socket
import threading
import queue
import time
import random
import logging
from dataclasses import dataclass
from typing import Dict, List


# Frame structure for GoBack-N protocol
@dataclass
class Frame:
    seq_num: int  # Sequence number of the frame
    ack_num: int  # Acknowledgment number for received frames
    payload: str  # Data being transmitted in the frame
    is_ack: bool = (
        False  # Boolean flag indicating whether this frame is an acknowledgment frame
    )


# NetworkEntity simulates packet generation at random time intervals
class NetworkEntity:
    def _init_(
        self, packet_delay_min: float, packet_delay_max: float, total_packets: int
    ):
        # Initialization of packet generator with parameters
        self.outgoing_queue = queue.Queue()  # Queue to hold outgoing packets
        self.packet_counter = 0  # Counter to track the number of packets generated
        self.delay_min = packet_delay_min  # Minimum packet generation delay
        self.delay_max = packet_delay_max  # Maximum packet generation delay
        self.total_packets = total_packets  # Total number of packets to generate
        self.running = True  # Flag to keep packet generation running

    # Packet generation method with random delay between packets
    def generate_packets(self):
        while self.running and self.packet_counter < self.total_packets:
            delay = random.uniform(
                self.delay_min, self.delay_max
            )  # Random delay within the range
            time.sleep(delay)  # Sleep for the random delay
            packet = f"Packet_{self.packet_counter}"  # Create a packet with a unique identifier
            self.outgoing_queue.put(packet)  # Put the generated packet in the queue
            logging.info(f"Generated packet: {packet}")
            self.packet_counter += 1  # Increment the packet counter


# DataLinkEntity simulates GoBack-N data link layer
class DataLinkEntity:
    def _init_(
        self,
        host,
        port,
        peer_host,
        peer_port,
        drop_prob,
        delay_min,
        delay_max,
        packet_delay_min,
        packet_delay_max,
        total_packets,
    ):
        # Initialization of data link layer entity with given parameters
        self.host = host
        self.port = port
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.drop_prob = drop_prob  # Probability of dropping a packet
        self.delay_min = delay_min  # Minimum network delay
        self.delay_max = delay_max  # Maximum network delay
        self.packet_delay_min = packet_delay_min  # Minimum packet generation delay
        self.packet_delay_max = packet_delay_max  # Maximum packet generation delay
        self.window_size = 7  # Size of the sliding window in GoBack-N protocol
        self.mod = 8  # Modulo for sequence numbers, i.e., sequence numbers will wrap around after 8
        self.timeout = 1.0  # Timeout period for retransmissions

        # State variables for GoBack-N protocol
        self.base = 0  # Sequence number of the first unacknowledged frame
        self.next_seq_num = 0  # Sequence number for the next frame to send
        self.expected_seq_num = 0  # Sequence number expected by the receiver
        self.frames_sent: Dict[int, tuple[Frame, float, int]] = (
            {}
        )  # Dictionary to keep track of sent frames
        self.frame_delivery_times: List[float] = (
            []
        )  # List to store the delivery times of frames
        self.successful_deliveries = 0  # Counter for successful frame deliveries

        # Create a NetworkEntity to simulate packet generation
        self.network_entity = NetworkEntity(
            packet_delay_min, packet_delay_max, total_packets
        )
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )  # Create a UDP socket for communication
        self.socket.bind((host, port))  # Bind the socket to the local address and port
        self.running = True  # Flag to keep the DataLinkEntity running
        self.lock = threading.Lock()  # Lock to ensure thread safety
        self.start_threads()  # Start background threads for different tasks

    # Start background threads for packet generation, receiving frames, sending frames, and timer
    def start_threads(self):
        threading.Thread(
            target=self.network_entity.generate_packets, daemon=True
        ).start()  # Packet generation thread
        threading.Thread(
            target=self.receive_frames, daemon=True
        ).start()  # Frame receiving thread
        threading.Thread(
            target=self.send_frames, daemon=True
        ).start()  # Frame sending thread
        threading.Thread(
            target=self.timer_thread, daemon=True
        ).start()  # Timer thread for retransmissions

    # Sending frames with GoBack-N protocol logic
    def send_frames(self):
        while self.running:
            with self.lock:
                # Send frames until the window size is filled or there are no more packets to send
                while (
                    self.next_seq_num < self.base + self.window_size
                    and not self.network_entity.outgoing_queue.empty()
                ):
                    packet = (
                        self.network_entity.outgoing_queue.get()
                    )  # Get the next packet from the queue
                    frame = Frame(
                        seq_num=self.next_seq_num
                        % self.mod,  # Wrap the sequence number around after 8
                        ack_num=self.expected_seq_num,  # Set the expected acknowledgment number
                        payload=packet,  # Set the payload of the frame
                    )
                    if frame.seq_num not in self.frames_sent:
                        self.frames_sent[frame.seq_num] = (
                            frame,
                            time.time(),
                            1,
                        )  # Track the frame with timestamp and retransmit count
                        self.send_frame(frame)  # Send the frame
                        logging.info(f"Entity {self.port}: Sent frame: {frame}")
                        self.next_seq_num += 1  # Increment the next sequence number
            time.sleep(0.01)  # Sleep briefly to allow other tasks to run

    # Sending a single frame (with possible packet loss and delay)
    def send_frame(self, frame: Frame):
        if (
            random.random() < self.drop_prob
        ):  # Simulate packet drop based on the probability
            logging.info(f"Entity {self.port}: Frame dropped: {frame}")
            return

        delay = random.uniform(self.delay_min, self.delay_max)  # Random network delay
        time.sleep(delay)  # Simulate the delay
        try:
            self.socket.sendto(
                str(frame._dict_).encode(), (self.peer_host, self.peer_port)
            )  # Send frame over UDP socket
            logging.info(f"Entity {self.port}: Sent frame: {frame}")
        except Exception as e:
            logging.error(f"Entity {self.port}: Error sending frame: {e}")

    # Handling acknowledgment frames from the receiver
    def handle_ack(self, frame: Frame):
        with self.lock:
            if frame.ack_num >= (
                self.base % self.mod
            ):  # Check if the ACK is for a valid frame
                logging.info(f"Entity {self.port}: Received ACK: {frame}")
                advance = (frame.ack_num - (self.base % self.mod)) % self.mod + 1
                for _ in range(advance):
                    if self.base % self.mod in self.frames_sent:
                        frame_info = self.frames_sent[
                            self.base % self.mod
                        ]  # Get frame info from the dictionary
                        delivery_time = (
                            time.time() - frame_info[1]
                        )  # Calculate delivery time
                        self.frame_delivery_times.append(
                            delivery_time
                        )  # Store the delivery time
                        self.successful_deliveries += (
                            1  # Increment successful delivery count
                        )
                        del self.frames_sent[
                            self.base % self.mod
                        ]  # Remove acknowledged frame from dictionary
                    self.base += 1  # Move the window forward

    # Handling data frames from the sender
    def handle_data(self, frame: Frame):
        logging.info(f"Entity {self.port}: Received data frame: {frame}")
        if (
            frame.seq_num == self.expected_seq_num
        ):  # Check if this is the expected frame
            self.network_entity.outgoing_queue.put(
                frame.payload
            )  # Put the payload into the queue for further processing
            self.expected_seq_num = (
                self.expected_seq_num + 1
            ) % self.mod  # Update expected sequence number
            ack_frame = Frame(
                seq_num=0,
                ack_num=(self.expected_seq_num - 1)
                % self.mod,  # Acknowledge the previous frame
                payload="",
                is_ack=True,
            )
            self.send_frame(ack_frame)  # Send the acknowledgment
            logging.info(f"Entity {self.port}: Sent ACK: {ack_frame}")
        else:  # If the frame is out of order, send the last valid ACK again
            ack_frame = Frame(
                seq_num=0,
                ack_num=(self.expected_seq_num - 1) % self.mod,
                payload="",
                is_ack=True,
            )
            self.send_frame(ack_frame)
            logging.info(f"Entity {self.port}: Sent ACK: {ack_frame}")

    # Timer thread that handles retransmissions for timed-out frames
    def timer_thread(self):
        while self.running:
            with self.lock:
                current_time = time.time()  # Get the current time
                for seq_num in list(
                    self.frames_sent.keys()
                ):  # Loop through all sent frames
                    frame, send_time, retransmit_count = self.frames_sent[seq_num]
                    if (
                        current_time - send_time > self.timeout
                    ):  # Check if the frame has timed out
                        self.frames_sent[seq_num] = (
                            frame,
                            current_time,
                            retransmit_count + 1,  # Increment retransmission count
                        )
                        self.send_frame(frame)  # Retransmit the frame
            time.sleep(0.1)  # Sleep briefly to reduce CPU usage

    # Receiving frames (both data and acknowledgment)
    def receive_frames(self):
        while self.running:
            try:
                data, _ = self.socket.recvfrom(1024)  # Receive data from the socket
                frame_dict = eval(
                    data.decode()
                )  # Convert received data to a dictionary
                frame = Frame(**frame_dict)  # Create a Frame object from the dictionary
                if frame.is_ack:  # If the frame is an ACK, handle it
                    self.handle_ack(frame)
                else:  # If the frame is a data frame, handle it
                    self.handle_data(frame)
            except Exception as e:
                if self.running:
                    logging.error(f"Entity {self.port}: Error receiving frame: {e}")
                continue

    # Get statistics like average delay and the number of retransmissions
    def get_statistics(self):
        avg_delay = (
            sum(self.frame_delivery_times) / len(self.frame_delivery_times)
            if self.frame_delivery_times
            else 0
        )
        total_retransmissions = sum(info[2] for info in self.frames_sent.values())
        avg_sends = (total_retransmissions + self.successful_deliveries) / max(
            1, self.successful_deliveries
        )
        return avg_delay, avg_sends

    # Stop the simulation and close the socket
    def stop(self):
        self.running = False
        self.network_entity.running = False
        self.socket.close()


# Run the simulation with given parameters
def run_simulation(
    packet_count,
    drop_prob,
    network_delay_min,
    network_delay_max,
    packet_delay_min,
    packet_delay_max,
):
    logging.info(f"\nRunning simulation with parameters:")
    logging.info(f"Packet Count: {packet_count}")
    logging.info(f"Drop Probability: {drop_prob}")
    logging.info(
        f"Network Delay Range: {network_delay_min:.2f}s - {network_delay_max:.2f}s"
    )
    logging.info(
        f"Packet Generation Delay Range: {packet_delay_min:.2f}s - {packet_delay_max:.2f}s"
    )

    # Instantiate two data link entities (representing sender and receiver)
    entity1 = DataLinkEntity(
        host="127.0.0.1",
        port=5000,
        peer_host="127.0.0.1",
        peer_port=5001,
        drop_prob=drop_prob,
        delay_min=network_delay_min,
        delay_max=network_delay_max,
        packet_delay_min=packet_delay_min,
        packet_delay_max=packet_delay_max,
        total_packets=packet_count,
    )

    entity2 = DataLinkEntity(
        host="127.0.0.1",
        port=5001,
        peer_host="127.0.0.1",
        peer_port=5000,
        drop_prob=drop_prob,
        delay_min=network_delay_min,
        delay_max=network_delay_max,
        packet_delay_min=packet_delay_min,
        packet_delay_max=packet_delay_max,
        total_packets=packet_count,
    )

    time.sleep(60)  # Simulate for 60 seconds or until all packets are processed

    entity1.stop()
    entity2.stop()

    # Get and print the statistics of both entities
    avg_delay1, avg_sends1 = entity1.get_statistics()
    avg_delay2, avg_sends2 = entity2.get_statistics()

    logging.info(f"Average delay for Entity 1: {avg_delay1:.3f} seconds")
    logging.info(f"Average sends for Entity 1: {avg_sends1:.3f}")
    logging.info(f"Average delay for Entity 2: {avg_delay2:.3f} seconds")
    logging.info(f"Average sends for Entity 2: {avg_sends2:.3f}")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filename="logs.log",
    filemode="w",
)
# Test the simulation with example parameters
run_simulation(
    packet_count=30,
    drop_prob=0.1,
    network_delay_min=0.2,
    network_delay_max=0.4,
    packet_delay_min=0.1,
    packet_delay_max=0.2,
)
