from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..buffer import Buffer, size_uint_var
from ..tls import Epoch
from .crypto import CryptoPair
from .logger import QuicLoggerTrace
from .packet import (
    NON_ACK_ELICITING_FRAME_TYPES,
    NON_IN_FLIGHT_FRAME_TYPES,
    PACKET_NUMBER_MAX_SIZE,
    PACKET_TYPE_HANDSHAKE,
    PACKET_TYPE_INITIAL,
    PACKET_TYPE_MASK,
    PACKET_TYPE_ZERO_RTT,
    QuicFrameType,
    is_long_header,
)

PACKET_MAX_SIZE = 1280
PACKET_LENGTH_SEND_SIZE = 2
PACKET_NUMBER_SEND_SIZE = 4 # EDITED here, was 2 before


QuicDeliveryHandler = Callable[..., None]


class QuicDeliveryState(Enum):
    ACKED = 0
    LOST = 1
    EXPIRED = 2


@dataclass
class QuicSentPacket:
    epoch: Epoch
    in_flight: bool
    is_ack_eliciting: bool
    is_crypto_packet: bool
    packet_number: int
    packet_type: int
    sent_time: Optional[float] = None
    sent_bytes: int = 0

    delivery_handlers: List[Tuple[QuicDeliveryHandler, Any]] = field(
        default_factory=list
    )
    quic_logger_frames: List[Dict] = field(default_factory=list)


class QuicPacketBuilderStop(Exception):
    pass

# ADDED here
# enum for malformed packet type
class MalformedPacketType(Enum):
    EMPTY_PACKET = 1
    UNEXPECTED_FRAME = 2

# EDITED HERE for padding
class QuicPacketBuilder:
    """
    Helper for building QUIC packets.
    """

    def __init__(
        self,
        *,
        host_cid: bytes,
        peer_cid: bytes,
        version: int,
        is_client: bool,
        packet_number: int = 0,
        peer_token: bytes = b"",
        quic_logger: Optional[QuicLoggerTrace] = None,
        spin_bit: bool = False,
        padInitialACK = 1,
        padAllInitialPackets = 1,
        malformedPacketType = None,
    ):
        self.max_flight_bytes: Optional[int] = None
        self.max_total_bytes: Optional[int] = None
        self.quic_logger_frames: Optional[List[Dict]] = None

        self._host_cid = host_cid
        self._is_client = is_client
        self._peer_cid = peer_cid
        self._peer_token = peer_token
        self._quic_logger = quic_logger
        self._spin_bit = spin_bit
        self._version = version

        # assembled datagrams and packets
        self._datagrams: List[bytes] = []
        self._datagram_flight_bytes = 0
        self._datagram_init = True
        self._packets: List[QuicSentPacket] = []
        self._flight_bytes = 0
        self._total_bytes = 0

        # current packet
        self._header_size = 0
        self._packet: Optional[QuicSentPacket] = None
        self._packet_crypto: Optional[CryptoPair] = None
        self._packet_long_header = False
        self._packet_number = packet_number
        self._packet_start = 0
        self._packet_type = 0

        self._buffer = Buffer(PACKET_MAX_SIZE)
        self._buffer_capacity = PACKET_MAX_SIZE
        self._flight_capacity = PACKET_MAX_SIZE

        # ADDED HERE
        self.padAllInitialPackets = padAllInitialPackets
        self.padInitialACK = padInitialACK
        self.frameInPacket = [] # use to keep track what frame is in the packet right now
        self.malformedPacketType = malformedPacketType

    @property
    def packet_is_empty(self) -> bool:
        """
        Returns `True` if the current packet is empty.
        """
        assert self._packet is not None
        packet_size = self._buffer.tell() - self._packet_start
        return packet_size <= self._header_size

    @property
    def packet_number(self) -> int:
        """
        Returns the packet number for the next packet.
        """
        return self._packet_number

    @property
    def remaining_buffer_space(self) -> int:
        """
        Returns the remaining number of bytes which can be used in
        the current packet.
        """
        return (
            self._buffer_capacity
            - self._buffer.tell()
            - self._packet_crypto.aead_tag_size
        )

    @property
    def remaining_flight_space(self) -> int:
        """
        Returns the remaining number of bytes which can be used in
        the current packet.
        """
        return (
            self._flight_capacity
            - self._buffer.tell()
            - self._packet_crypto.aead_tag_size
        )

    def flush(self) -> Tuple[List[bytes], List[QuicSentPacket]]:
        """
        Returns the assembled datagrams.
        """
        if self._packet is not None:
            self._end_packet()
        self._flush_current_datagram()

        datagrams = self._datagrams
        packets = self._packets
        self._datagrams = []
        self._packets = []
        return datagrams, packets

    def start_frame(
        self,
        frame_type: int,
        capacity: int = 1,
        handler: Optional[QuicDeliveryHandler] = None,
        handler_args: Sequence[Any] = [],
    ) -> Buffer:
        """
        Starts a new frame.
        """
        if self.remaining_buffer_space < capacity or (
            frame_type not in NON_IN_FLIGHT_FRAME_TYPES
            and self.remaining_flight_space < capacity
        ):
            raise QuicPacketBuilderStop

        self._buffer.push_uint_var(frame_type)
        if frame_type not in NON_ACK_ELICITING_FRAME_TYPES:
            self._packet.is_ack_eliciting = True
        if frame_type not in NON_IN_FLIGHT_FRAME_TYPES:
            self._packet.in_flight = True
        if frame_type == QuicFrameType.CRYPTO:
            self._packet.is_crypto_packet = True
        if handler is not None:
            self._packet.delivery_handlers.append((handler, handler_args))
        self.frameInPacket.append(frame_type) # ADDED HERE to track what frame is in the packet
        return self._buffer

    def start_packet(self, packet_type: int, crypto: CryptoPair, new_packet: bool = False) -> None:
        """
        Starts a new packet.
        """
        buf = self._buffer

        # finish previous datagram
        if self._packet is not None:
            self._end_packet()

        # if there is too little space remaining, start a new datagram
        # FIXME: the limit is arbitrary!
        # EDITED here start a new packet for Initial and Handshake packet
        packet_start = buf.tell()
        if(self._buffer_capacity - packet_start < 128 or new_packet):
            self._flush_current_datagram()
            packet_start = 0

        # initialize datagram if needed
        if self._datagram_init:
            if self.max_total_bytes is not None:
                remaining_total_bytes = self.max_total_bytes - self._total_bytes
                if remaining_total_bytes < self._buffer_capacity:
                    self._buffer_capacity = remaining_total_bytes

            self._flight_capacity = self._buffer_capacity
            if self.max_flight_bytes is not None:
                remaining_flight_bytes = self.max_flight_bytes - self._flight_bytes
                if remaining_flight_bytes < self._flight_capacity:
                    self._flight_capacity = remaining_flight_bytes
            self._datagram_flight_bytes = 0
            self._datagram_init = False

        # calculate header size
        packet_long_header = is_long_header(packet_type)
        if packet_long_header:
            # Original: Was 11 here because only 2 bytes for packet number length
            #header_size = 11 + len(self._peer_cid) + len(self._host_cid)

            # EDITED here
            # Header Form + Fixed Bit + Long Packet Type + Type-Specific Bits = 1 bytes
            # Version = 4 bytes
            # DCID Length = 1 byte
            # SCID Length = 1 byte
            # length = 2 bytes
            # packet number length = 4 bytes
            header_size = 13 + len(self._peer_cid) + len(self._host_cid)

            # for Initial packet only (check if there is a token)
            if (packet_type & PACKET_TYPE_MASK) == PACKET_TYPE_INITIAL:
                token_length = len(self._peer_token)
                header_size += size_uint_var(token_length) + token_length
        else:
            # Original: Was 3 here because only 2 bytes for packet number length
            #header_size = 3 + len(self._peer_cid)

            # EDITED here
            header_size = 5 + len(self._peer_cid)

        # check we have enough space
        if packet_start + header_size >= self._buffer_capacity:
            raise QuicPacketBuilderStop

        # determine ack epoch
        if packet_type == PACKET_TYPE_INITIAL:
            epoch = Epoch.INITIAL
        elif packet_type == PACKET_TYPE_HANDSHAKE:
            epoch = Epoch.HANDSHAKE
        else:
            epoch = Epoch.ONE_RTT

        self._header_size = header_size
        self._packet = QuicSentPacket(
            epoch=epoch,
            in_flight=False,
            is_ack_eliciting=False,
            is_crypto_packet=False,
            packet_number=self._packet_number,
            packet_type=packet_type,
        )
        self._packet_crypto = crypto
        self._packet_long_header = packet_long_header
        self._packet_start = packet_start
        self._packet_type = packet_type
        self.quic_logger_frames = self._packet.quic_logger_frames

        buf.seek(self._packet_start + self._header_size)

    # EDITED here
    def _end_packet(self) -> None:
        """
        Ends the current packet.
        """
        buf = self._buffer
        packet_size = buf.tell() - self._packet_start
        #print("packet size: " + str(packet_size))
        #print("header size: " + str(self._header_size))
        # EDITED here so that it will continue to send the empty payload packet
        if packet_size > self._header_size or self.malformedPacketType != None:
            if(self.malformedPacketType == None):
                # padding to ensure sufficient sample size
                padding_size = (
                    PACKET_NUMBER_MAX_SIZE
                    - PACKET_NUMBER_SEND_SIZE
                    + self._header_size
                    - packet_size
                )

                # pad Initial ACK packet
                if(QuicFrameType.ACK in self.frameInPacket):
                    if(self.padInitialACK and self._is_client and self._packet_type == PACKET_TYPE_INITIAL
                    and self.remaining_flight_space and self.remaining_flight_space > padding_size):
                        padding_size = self.remaining_flight_space
                # pad all other Initial ACK packet
                else:
                    if(self.padAllInitialPackets and self._is_client and self._packet_type == PACKET_TYPE_INITIAL 
                    and self.remaining_flight_space and self.remaining_flight_space > padding_size):
                        padding_size = self.remaining_flight_space

                # padding for initial datagram
                # EDITED HERE
                """if(self.padAllInitialPackets):
                    if (
                    self._is_client
                    and self._packet_type == PACKET_TYPE_INITIAL
                    and self.remaining_flight_space
                    and self.remaining_flight_space > padding_size
                    ):
                        padding_size = self.remaining_flight_space
                else:
                    if (
                    self._is_client
                    and self._packet_type == PACKET_TYPE_INITIAL
                    and self._packet.is_ack_eliciting
                    #and not self._packet.is_ack_eliciting # EDITED HERE for sending cltHello without padding
                    and self.remaining_flight_space
                    and self.remaining_flight_space > padding_size
                    ):
                        padding_size = self.remaining_flight_space"""

                # write padding
                if padding_size > 0:
                    buf.push_bytes(bytes(padding_size))
                    packet_size += padding_size
                    self._packet.in_flight = True

                    # log frame
                    if self._quic_logger is not None:
                        self._packet.quic_logger_frames.append(
                            self._quic_logger.encode_padding_frame()
                        )
            # ADDED here
            # push frame type 0xff to the packet
            elif(self.malformedPacketType == MalformedPacketType.UNEXPECTED_FRAME):
                    buf.push_bytes(b'\xff') # b'0xff' for picoquic bufferoverflow
                    buf.push_bytes(b'\xff')
                    packet_size += 2

            #elif(self.malformedPacketType == MalformedPacketType.EMPTY_PACKET):
            #    buf.push_bytes(bytes(1230))
            #    packet_size += 1230

            # write header
            if self._packet_long_header:
                length = (
                    packet_size
                    - self._header_size
                    + PACKET_NUMBER_SEND_SIZE
                    + self._packet_crypto.aead_tag_size
                )

                buf.seek(self._packet_start)
                buf.push_uint8(self._packet_type | (PACKET_NUMBER_SEND_SIZE - 1))
                buf.push_uint32(self._version)
                buf.push_uint8(len(self._peer_cid))
                buf.push_bytes(self._peer_cid)
                buf.push_uint8(len(self._host_cid))
                buf.push_bytes(self._host_cid)
                if (self._packet_type & PACKET_TYPE_MASK) == PACKET_TYPE_INITIAL:
                    buf.push_uint_var(len(self._peer_token))
                    buf.push_bytes(self._peer_token)
                buf.push_uint16(length | 0x4000)
                # EDITED here, push 4 bytes of packet number
                buf.push_uint32(self._packet_number & 0xFFFFFFFF)
            else:
                buf.seek(self._packet_start)
                buf.push_uint8(
                    self._packet_type
                    | (self._spin_bit << 5)
                    | (self._packet_crypto.key_phase << 2)
                    | (PACKET_NUMBER_SEND_SIZE - 1)
                )
                buf.push_bytes(self._peer_cid)
                # EDITED here, push 4 bytes of packet number
                buf.push_uint32(self._packet_number & 0xFFFFFFFF)

            # encrypt in place
            plain = buf.data_slice(self._packet_start, self._packet_start + packet_size)
            buf.seek(self._packet_start)
            buf.push_bytes(
                self._packet_crypto.encrypt_packet(
                    plain[0 : self._header_size],
                    plain[self._header_size : packet_size],
                    self._packet_number,
                )
            )
            self._packet.sent_bytes = buf.tell() - self._packet_start
            self._packets.append(self._packet)
            if self._packet.in_flight:
                self._datagram_flight_bytes += self._packet.sent_bytes

            # short header packets cannot be coallesced, we need a new datagram
            if not self._packet_long_header:
                self._flush_current_datagram()

            self._packet_number += 1
        else:
            # "cancel" the packet
            buf.seek(self._packet_start)

        self._packet = None
        self.quic_logger_frames = None

    def _flush_current_datagram(self) -> None:
        datagram_bytes = self._buffer.tell()
        if datagram_bytes:
            self._datagrams.append(self._buffer.data)
            self._flight_bytes += self._datagram_flight_bytes
            self._total_bytes += datagram_bytes
            self._datagram_init = True
            self._buffer.seek(0)
