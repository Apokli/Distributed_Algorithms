from abstractprocess import AbstractProcess, Message
from collections import defaultdict
from test_cases import test_events
from time import perf_counter

class MessageQueue:
    """
    Class for the message Queue. Maintains received messages in time order (latest at the right)
    
    """

    def __init__(self):
        self.q = []

    def is_empty(self):
        return len(self.q) == 0

    def receive(self, msg):
        if msg.form != "ACK":
            if not self.q:
                self.q.append(msg)
            else:
                for i in range(len(self.q) - 1, -1, -1):
                    tmp_msg = self.q[i]
                    if msg.timestamp < tmp_msg.timestamp or (msg.timestamp == tmp_msg.timestamp and msg.sender < tmp_msg.sender):
                        self.q.insert(i + 1, msg)
                        break
                else:
                    self.q.insert(0, msg)

    def deliver(self):
        return self.q.pop()

    def get_latest_message(self):
        if self.is_empty():
            return None
        return self.q[-1]

class TotalOrderingProcess(AbstractProcess):
    def __init__(self, pid, addresses):
        super().__init__(pid, addresses)
        self.test_clock = 0         # loop counter
        self.test_events = dict()   # test case events for this node
        self.LSC = 0                # Local Scalar Clock
        self.collected_acks = defaultdict(set)  # dictionary to record acknowledgements regarding each received message
        self.message_queue = MessageQueue()     # the local message queue
        self.delivered_msg = []                 # For final printing, simply stores all contents delivered in time order
        self.load_test_events()                 # Load tests from "total_ordering.py"
        self.start = perf_counter()             # For ensuring the algorithm runs for a while

    def load_test_events(self):
        self.test_events = test_events[self.idx]
        print(f"(ID:{self.idx}) test events: {self.test_events}")

    # generate acknowledgement messages according to the received message
    def generate_ack(self, msg):
        return Message("ACK", f"{msg.sender}, {msg.timestamp}", self.idx, self.LSC)

    # Scalar clock increment rules
    def increment_clock(self, msg=None):
        if not msg:
            self.LSC += 1
        else:
            self.LSC = max(self.LSC, msg.timestamp) + 1

    # broadcast message to everyone
    async def broadcast(self, msg):
        for dest in self.addresses.keys():
            await self.send_message(msg, dest)

    # receiving a message
    def receive(self):
        msg: Message = self.buffer.get()
        self.increment_clock(msg)
        # print(f'{self.idx} Got {msg.form} "{msg.content}" from process {msg.sender} sent at LSC {msg.timestamp}')
        self.message_queue.receive(msg)
        return msg

    # delivering a message
    def deliver(self):
        msg = self.message_queue.deliver()
        self.delivered_msg.append(msg.content)
        return msg

    # run test case
    async def run_test(self):
        if self.test_clock in self.test_events.keys():
            self.increment_clock()
            msg = Message("MSG", self.test_events[self.test_clock], self.idx, self.LSC)
            await self.broadcast(msg)

    async def algorithm(self):
        
        self.test_clock += 1
        await self.run_test()

        if self.buffer.has_messages():
            # Retrieve message
            msg = self.receive()
            # if message is not an acknowledgement, then send an acknowledgement
            if msg.form != "ACK":
                self.increment_clock()
                ack_msg = self.generate_ack(msg)
                await self.broadcast(ack_msg)
            # if message is an acknowledgement, then store it in the collected acks
            else:
                host, timestamp = list(map(int, msg.content.split(", ")))
                self.collected_acks[(host, timestamp)].add(msg.sender)
            
        # deliver
        lm = self.message_queue.get_latest_message()
        if lm and len(self.collected_acks[(lm.sender, lm.timestamp)]) == len(self.addresses):
            delivered = self.deliver()
            print(f"(ID:{self.idx}) delivered message {delivered.content} from sender: {delivered.sender} sent at {delivered.timestamp}")
        
        # end
        if not perf_counter() - self.start < 2:     # to ensure the algorithm does not end immediately
            if perf_counter() - self.start > 30 and self.message_queue.is_empty():  # all delivered
                print(f"(ID:{self.idx}) delivered:", "".join(self.delivered_msg))   # print every message
                print('Exiting algorithm')
                self.running = False
