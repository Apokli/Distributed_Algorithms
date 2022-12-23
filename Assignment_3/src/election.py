from abstractprocess import AbstractProcess, Message
from test_cases import test_events
import random


class ElectionProcess(AbstractProcess):
    def __init__(self, pid, addresses):
        super().__init__(pid, addresses)
        self.test_clock = 0         # loop counter
        self.test_events = dict()   # test case events for this node

        self.tracking = self.idx
        self.parent = None
        self.potential_parent = None
        self.level = -1

        self.is_candidate = False
        self.candidate_receiving = False
        self.untraversed = [id for id in addresses.keys()]
        self.killed = False
        self.elected = False

        self.load_test_events()                 # Load tests from "total_ordering.py"

    def compare(self, level, idx):
        if self.level > level: return -1
        elif self.level < level: return 1
        else:
            if self.tracking > idx: return -1
            elif self.tracking < idx: return 1
            else: return 0

    async def ordinary_p(self, level, owner_id, idx):
        comparison = self.compare(level, owner_id)

        if comparison > 0:
            print(f"(ID: {self.idx}) preparing to be captured by (ID: {idx})")
            self.killed = True
            self.potential_parent = owner_id
            self.tracking = owner_id
            self.level = level
            if not self.parent:
                self.parent = self.potential_parent
                print(f"(ID: {self.idx}) captured by (ID: {idx})")
            msg = Message(1, level, owner_id, self.idx)
            await self.send_message(msg, self.parent)


        elif comparison == 0:
            print(f"(ID: {self.idx}) received OK from previous parent (ID: {self.parent}), captured by (ID: {self.potential_parent})")
            self.parent = self.potential_parent
            msg = Message(1, level, owner_id, self.idx)
            await self.send_message(msg, self.parent)

    async def candidate_p(self, level=None, owner_id=None, idx=None):
        if self.untraversed:
            if not self.candidate_receiving:
                send_id = random.choice(self.untraversed)
                msg = Message(0, self.level, self.idx, self.idx)
                self.candidate_receiving = True
                await self.send_message(msg, send_id)
                print(f"(ID: {self.idx}) sending ({self.level, self.idx}) to node {send_id} to capture it")
            # when really received a message
            elif level is not None:
                if self.idx == owner_id and not self.killed:
                    print(f"(ID: {self.idx}) received acknowledgement from (ID: {idx})")
                    self.level += 1
                    self.untraversed.remove(idx)
                    self.candidate_receiving = False
                else:
                    if self.compare(level, owner_id) >= 0:
                        print(f"(ID: {self.idx}) received kill from (ID: {idx})")
                        msg = Message(0, level, owner_id, self.idx)
                        await self.send_message(msg, idx)
                        self.killed = True

        if not self.killed and not self.untraversed:
            self.elected = True
            print(f"<<<<<<<<<<(Node {self.idx}) has been elected with (level {self.level})>>>>>>>>>")
            msg = Message(2, self.level, self.idx, self.idx)
            for id in self.addresses.keys():
                await self.send_message(msg, id)    # send marker
            self.running = False

    def load_test_events(self):
        self.test_events = test_events[self.idx]

    # run test case
    async def run_test(self):
        if self.test_clock in self.test_events.keys():
            msg_content = self.test_events[self.test_clock]
            if msg_content == "start":
                if self.parent is None:
                    print(f"\n ---- ==== election initiated by {self.idx} ==== ---- \n")
                    self.level = 0
                    self.is_candidate = True
                else:
                    print(f"\n (ID: {self.idx}) cannot start election because he has already been captured \n")

    async def algorithm(self):
        self.test_clock += 1
        await self.run_test()

        if self.is_candidate:
            await self.candidate_p()

        if self.buffer.has_messages():
            msg: Message = self.buffer.get()
            process, level, owner_id, idx = msg.receiver, msg.level, msg.owner_id, msg.sender
            if process == 0:
                await self.ordinary_p(level, owner_id, idx)
            elif process == 1:
                await self.candidate_p(level, owner_id, idx)
            # When someone has been elected
            else:
                print(f"(ID:{self.idx}) has known that (ID:{idx}) is the leader! Terminating...")
                self.running = False
