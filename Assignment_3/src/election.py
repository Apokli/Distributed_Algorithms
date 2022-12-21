from abstractprocess import AbstractProcess, Message
from test_cases import test_events
import random


class ElectionProcess(AbstractProcess):
    def __init__(self, pid, addresses):
        super().__init__(pid, addresses)
        self.test_clock = 0         # loop counter
        self.test_events = dict()   # test case events for this node


        self.tracking = 0
        self.parent = None
        self.potential_parent = None
        self.level = 0

        self.is_candidate = False
        self.candidate_receiving = False
        self.untraversed = [id for id in addresses.keys()]
        self.killed = False
        self.elected = False

        self.load_test_events()                 # Load tests from "total_ordering.py"

    def compare(self, level, idx):
        if self.level < level: return -1
        elif self.level > level: return 1
        else:
            if self.tracking < idx: return -1
            elif self.tracking > idx: return 1
            else: return 0

    async def ordinary_p(self, level, idx):
        comparison = self.compare(level, idx)

        if comparison > 0:
            self.potential_parent = idx
            self.tracking = idx
            self.level = level
            if not self.parent:
                self.parent = self.potential_parent
            msg = Message(1, level, self.tracking)
            await self.send_message(msg, self.parent)

        elif comparison == 0:
            self.parent = self.potential_parent
            msg = Message(1, level, idx)
            await self.send_message(msg, self.parent)

    async def candidate_p(self, level=None, idx=None):
        if self.untraversed:
            if not self.candidate_receiving:
                send_id = random.choice(self.untraversed)
                msg = Message(0, self.level, self.idx)
                self.candidate_receiving = True
                await self.send_message(msg, send_id)
            else:
                comparison = self.compare(level, idx)
                if self.idx == idx and not self.killed:
                    self.level += 1
                    self.untraversed.remove(idx)
                    self.candidate_receiving = False
                else:
                    if comparison >= 0:
                        self.killed = True

        if not self.killed and not self.untraversed:
            self.elected = True

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

        if self.is_candidate:
            await self.candidate_p()

        if self.buffer.has_messages():
            msg: Message = self.buffer.get()
            process, level, idx = msg.receiver, msg.level, msg.sender
            if process == 0:
                await self.ordinary_p(level, idx)
            else:
                await self.candidate_p(level, idx)

        
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
