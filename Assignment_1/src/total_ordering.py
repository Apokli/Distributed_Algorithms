from abstractprocess import AbstractProcess, Message

class TotalOrderingProcess(AbstractProcess):
    def __init__(self, pid, addresses):
        super().__init__(pid, addresses)
        self.LSC = 0    # Local Scalar Clocks
        self.first_cycle = True
        self.pending_acks = []

    def generate_ack(self, msg):
        return Message("ACK", f"{msg.sender}, {msg.timestamp}", self.idx, self.LSC)

    def increment_clock(self, msg=None):
        if not msg:
            self.LSC += 1
        else:
            self.LSC = max(self.LSC, msg.timestamp) + 1

    async def algorithm(self):
        if self.first_cycle:
            self.increment_clock()
            msg = Message("MSG", f"Hello world", self.idx, self.LSC)
            to = list(self.addresses.keys())[0]
            await self.send_message(msg, to)
            self.pending_acks.append(self.LSC)
            self.first_cycle = False

        if self.buffer.has_messages():
            # Retrieve message
            msg: Message = self.buffer.get()
            self.increment_clock(msg)
            print(f'Got {msg.form} "{msg.content}" from process {msg.sender} at LSC {self.LSC}')
            # Compose echo message
            if msg.form != "ACK":
                self.increment_clock()
                ack_msg = self.generate_ack(msg)
                await self.send_message(ack_msg, msg.sender)
            else:
                host, id = list(map(int, msg.content.split(", ")))
                if host == self.idx and id in self.pending_acks:
                    self.pending_acks.remove(id)
        
        else:
            if not self.pending_acks:
                print('Exiting algorithm')
                self.running = False
