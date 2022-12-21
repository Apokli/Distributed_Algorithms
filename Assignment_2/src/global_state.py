from abstractprocess import AbstractProcess, Message
from test_cases import test_events

class LocalRecord:
    def __init__(self, addresses):
        self.money = 0
        self.self_recorded = False
        self.channel_open = dict()
        self.channel_buffers = dict()
        for id in addresses.keys():
            self.channel_open[id] = False
            self.channel_buffers[id] = []


class GlobalStateProcess(AbstractProcess):
    def __init__(self, pid, addresses):
        super().__init__(pid, addresses)
        self.test_clock = 0         # loop counter
        self.test_events = dict()   # test case events for this node

        self.money = 10000
        self.local_record = LocalRecord(addresses)
        self.record_done = True
        self.load_test_events()                 # Load tests from "total_ordering.py"

        # For stopping the algorithm
        self.term = False
        self.term_acks = 0

    # propagate the global state recording attempt
    async def record_and_send_markers(self, src_id):
        self.local_record.money = self.money
        self.local_record.self_recorded = True
        self.record_done = False
        msg = Message("MAR", "", self.idx)
        for id in self.addresses.keys():
            await self.send_message(msg, id)    # send marker
            if id != src_id:
                self.local_record.channel_open[id] = True   # open channel buffer

    # receiving a message
    async def receive_and_act(self):
        msg: Message = self.buffer.get()
        if msg.form == "MAR":
            print(f"(ID:{self.idx}) received MARKER from (ID:{msg.sender})")
            if not self.local_record.self_recorded:
                await self.record_and_send_markers(msg.sender)
            else:
                self.local_record.channel_open[msg.sender] = False
        elif msg.form == "TER":
            self.term_acks += 1
        else:
            if self.local_record.channel_open[msg.sender] == True:
                self.local_record.channel_buffers[msg.sender].append(msg)
            # add money
            words = msg.content.split()
            if words[0] == "Give":
                self.money += int(words[1])
                print(f"(ID:{self.idx}) received {words[1]} bucks from (ID:{msg.sender})")

    def load_test_events(self):
        self.test_events = test_events[self.idx]
        self.last_clock = list(self.test_events.keys())[-1]

    # run test case
    async def run_test(self):
        if self.test_clock in self.test_events.keys():
            msg_content = self.test_events[self.test_clock]
            if msg_content == "Initiate Record":
                print(f"\n\n ---- ==== Record initiated by {self.idx} ==== ---- \n\n")
                await self.record_and_send_markers(-1)
            else:
                words = msg_content.split()
                if words[0] == "Give":
                    self.money -= int(words[1])
                    print(f"(ID:{self.idx}) gave (ID:{int(words[-1])}) {words[1]} bucks")
                msg = Message("MSG", msg_content, self.idx)
                await self.send_message(msg, int(words[-1]))

            # Terminate Request
            if self.test_clock == self.last_clock:
                self.term = True
                for id in self.addresses.keys():
                    msg = Message("TER", "", self.idx)
                    await self.send_message(msg, id) 

    async def algorithm(self):
        self.test_clock += 1
        await self.run_test()

        if self.buffer.has_messages():
            await self.receive_and_act()

        # check if done recorded:
        if self.local_record.self_recorded:
            for id in self.addresses.keys():
                if self.local_record.channel_open[id]:
                    break
            else:
                self.record_done = True
        
        # end
        if self.term and self.term_acks == len(self.addresses) and self.local_record.self_recorded and self.record_done:     # really ends
            print(f"(ID:{self.idx}) has done recording")
            print(f"(ID:{self.idx}) has money: {self.local_record.money}")
            for id in self.addresses.keys():
                print(f"Channel {id}:")
                for msg in self.local_record.channel_buffers[id]:
                    print(msg.content)
                print("Done!")
            self.running = False
