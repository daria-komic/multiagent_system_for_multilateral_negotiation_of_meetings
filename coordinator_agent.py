import asyncio
import json
import math
from spade import agent, behaviour
from spade.message import Message

class CoordinatorAgent(agent.Agent):
    class SchedulerBehaviour(behaviour.CyclicBehaviour):
        async def on_start(self):
            print(f"Hello, I am {self.agent.jid} the coordinator of this meeting. You will be receiving the details to the meeting shortly.")
        
        async def run(self):
            with open('meeting_details.json', 'r') as json_file:
                meetings = json.load(json_file)

            with open("user_agents.txt", "r") as file:
                user_agents = [line.strip() for line in file.readlines()]

            message_printed = False

            for meeting in meetings:     
                for user in user_agents:
                    if "cancel" in meeting:
                        if not message_printed:
                            print("Coordinator: All meeting dates exhausted, cancelling current session.")
                            message_printed = True
                        end_msg = Message(
                            to=str(user),
                            body=json.dumps({"status": "cancel meeting"}),
                            metadata={"performative": "cancel"}
                        )
                        await self.send(end_msg)
                        await asyncio.sleep(2)
                        await self.agent.stop()

                start_time = meeting["start_time"]
                end_time = meeting["end_time"]
                date = meeting["date"]
                duration = meeting["duration_minutes"]
                meeting_type = meeting["type"]
                print("Sending meeting details now.")
                print(f"The earliest start of the meeting is at {start_time} and the latest finish time is by {end_time}. It will be held on the {date}, it will be {meeting_type} and it will last for {duration} minutes.")

                for user_agent in user_agents:
                    msg = Message(
                        to=user_agent,
                        body=json.dumps(meeting),
                        metadata={
                            "ontology": "meeting_details",
                            "performative": "inform"
                        },
                    )
                    await self.send(msg)
                    print(f"Sent meeting details to {user_agent}.")

                accepted = []
                rejected = []
                total_points = []
                for user_agent in user_agents:
                    msg = await self.receive(timeout=10)
                    if msg:
                        print(f"Coordinator received response from {msg.sender}.")
                        if msg.metadata['performative'] == 'inform':
                            try:
                                response = json.loads(msg.body)
                                status = response.get("availability_status", "")

                                if response.get("points", ""):
                                    points = response.get("points", "")
                                    total_points.append(points)                           

                                if status == "accept":
                                    accepted.append(msg.sender)
                                    print(f"User agent {msg.sender} accepted.")
                                else:
                                    rejected.append(msg.sender)
                                    print(f"User agent {msg.sender} rejected.")

                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON message from {msg.sender}: {e}")
                            except Exception as e:
                                print(f"Error processing message from {msg.sender}: {e}")
                        else:
                            print("Coordinator: Waiting for a message.")             

                for user in user_agents:
                    if len(accepted) >= len(user_agents) * 0.80:
                        if total_points:
                            avg_preference = sum(total_points) / len(user_agents)
   
                            variance = sum((point - avg_preference) ** 2 for point in total_points) / (len(total_points) - 1)

                            std_deviation = math.sqrt(variance)

                            group_utility = avg_preference - std_deviation

                            if not hasattr(self, 'utility'): 
                                print(f"Group utility: {group_utility}")
                            self.utility = True    

                        if not hasattr(self, 'confirmed'): 
                            print(f"Coordinator: Meeting confirmed with all participants.")
                        self.confirmed = True

                        confirmation_msg = Message(
                            to=user,
                            body=json.dumps({"status": "scheduled"}),
                            metadata={"performative": "agree"}
                        )
                        await self.send(confirmation_msg)
                        print(f"Coordinator: Confirmation message sent to {user}.")
                        await asyncio.sleep(2)                    
                    else:
                        if not hasattr(self, 'printed'):
                            print(f"Coordinator: Meeting could not be confirmed with most participants, suggesting new meeting details.")
                        self.printed = True

    async def setup(self):
        print(f"Coordinator agent starting.")
        behaviour_scheduler = self.SchedulerBehaviour()
        self.add_behaviour(behaviour_scheduler)
