import asyncio
import json
from datetime import datetime, timedelta
from spade import agent, behaviour
from spade.message import Message

class UserAgentOne(agent.Agent):    
    def __init__(self, jid, password, preference=False):
        super().__init__(jid, password)
        self.preference = preference

    def preference_function(self, start_time, end_time, date, difference_start, difference_end, meeting_duration, meeting_type):
        if self.preference == True:
            preferences = {"time" : 0.30, "date" : 0.10, "difference" : 0.20, "duration": 0.15, "week_day" : 0.10, "type": 0.15}
            date_str = datetime.strftime(date, "%Y-%m-%d")
            week_day = date.weekday()
            morning = datetime.strptime(date_str + " " + "12:00:00", "%Y-%m-%d %H:%M:%S")
            afternoon = datetime.strptime(date_str + " " + "16:00:00", "%Y-%m-%d %H:%M:%S")
            evening = datetime.strptime(date_str + " " + "20:00:00", "%Y-%m-%d %H:%M:%S")
            duration = meeting_duration
            five_minutes = timedelta(minutes=5)
            ten_minutes = timedelta(minutes=10)
            meet_type = meeting_type

            if week_day == 0:
                week_day_score = 5
            elif week_day == 1:
                week_day_score = 5
            elif week_day == 2:
                week_day_score = 9
            elif week_day == 3:
                week_day_score = 5
            elif week_day == 4:
                week_day_score = 9
            elif week_day == 5:
                week_day_score = 5
            else:
                week_day_score = 5
                        
            if start_time < morning and end_time <= morning:
                time_score = 9
            elif start_time >= morning and end_time <= afternoon:
                time_score = 5
            else:
                time_score = 1

            if date == "2024-08-27":
                date_score = 2
            elif date == "2024-08-30":
                date_score = 2
            elif date == "2024-09-05":
                date_score = 2 
            elif date == "2024-09-12":
                date_score = 2             
            else:
                date_score = 10    

            if difference_start == five_minutes or difference_end == five_minutes or difference_start == ten_minutes or difference_end == ten_minutes:
                difference_score = 2
            else:
                difference_score = 10

            if duration <= 15:
                duration_score = 3
            elif duration <= 30:
                duration_score = 5
            elif duration <= 60:
                duration_score = 9    
            else:
                duration_score = 4

            if meet_type == "virtual":
                type_score = 2
            if meet_type == "hybrid":
                type_score = 6
            else:
                type_score = 9                    

            value_time =  time_score * preferences["time"]
            value_date = date_score * preferences["date"]
            value_difference = difference_score * preferences["difference"]
            value_duration = duration_score * preferences["duration"]
            value_week_day = week_day_score * preferences["week_day"]
            value_type = type_score * preferences["type"]
            total_value = value_time + value_date + value_difference + value_duration + value_week_day + value_type
            print(f"Total preference score given by user {self.jid} is: {total_value:.2f}")

            return total_value  
        else:
            return None

    def accept_reject_meeting(self, start_time, end_time, date, difference_start, difference_end, meeting_duration, meeting_type):
        points = 0
        if self.preference == True:
            points = self.preference_function(start_time, end_time, date, difference_start, difference_end, meeting_duration, meeting_type)    
            if points >= 6.5:
                return "accept", points
            else:
                return "reject", points
        else:
            return None, None    
        
    class AvailabilityBehaviour(behaviour.CyclicBehaviour):
        async def on_start(self):
            print(f"I am agent number {self.agent.jid} and I'm ready to receive messages.")
            with open("user_agents.txt", "a") as file:
                file.write(f"{self.agent.jid}\n")
        
        async def run(self):
            with open('user1_calendar.json', 'r') as json_file:
                available_times = json.load(json_file)

            msg = await self.receive(timeout=10)
            if msg:
                if msg.metadata['performative'] == 'inform':
                    try:
                        meeting_details = json.loads(msg.body)
                        print(f"Agent {self.agent.jid} received meeting details.")

                        available = False

                        for time_slot in available_times:
                            start_time_str, end_time_str = time_slot['time_period'].split('-')
                            start_time = datetime.strptime(time_slot['date'] + " " + start_time_str, "%d/%m/%Y %H:%M:%S")
                            end_time = datetime.strptime(time_slot['date'] + " " + end_time_str, "%d/%m/%Y %H:%M:%S")
                            meeting_start = datetime.strptime(meeting_details['date'] + " " + meeting_details['start_time'], "%d/%m/%Y %H:%M:%S")
                            meeting_end = datetime.strptime(meeting_details['date'] + " " + meeting_details['end_time'], "%d/%m/%Y %H:%M:%S")
                            meeting_duration = meeting_details["duration_minutes"]
                            meeting_type = meeting_details["type"]

                            date = datetime.strptime(meeting_details["date"], "%d/%m/%Y")
                            difference_start = start_time - meeting_start 
                            difference_end = meeting_end - end_time

                            duration = end_time - start_time
                            seconds = duration.total_seconds()
                            total = seconds / 60   
                            total = int(total)                      

                            if time_slot['date'] == meeting_details['date']:
                                if(total >= meeting_details['duration_minutes']):
                                    ten_min = timedelta(minutes=10)
                                    if (start_time - ten_min <= meeting_start and end_time + ten_min >= meeting_end):
                                        if(difference_start <= ten_min or difference_end <= ten_min):    
                                            available = True
                                            break
                                                           
                        response, points = self.agent.accept_reject_meeting(meeting_start, meeting_end, date, difference_start, difference_end, meeting_duration, meeting_type) 

                        if response and points:
                            response_message = "accept" if available == True and response == "accept" else "reject"  

                            availability_msg = Message(
                            to="coordinator@localhost",
                            body=json.dumps({"availability_status": response_message, "points": points}),
                            metadata={"performative": "inform"}
                        )
                        else:
                            response_message = "accept" if available == True else "reject"

                            availability_msg = Message(
                            to="coordinator@localhost",
                            body=json.dumps({"availability_status": response_message}),
                            metadata={"performative": "inform"}
                        )          
                        
                        await self.send(availability_msg)
                        print(f"Agent {self.agent.jid} sent confirmation status to coordinator: {response_message}")     

                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON message {self.agent.jid}: {e}")
                    except Exception as e:
                        print(f"Error processing message {self.agent.jid}: {e}")
                                    
                if msg.metadata['performative'] == 'agree':
                    print(f"{self.agent.jid}: Great, adding it to my calendar.")
                    await self.agent.stop()
                elif msg.metadata['performative'] == 'cancel':
                    print(f"{self.agent.jid} stopping, because no consensus was reached.")
                    await self.agent.stop()     
            else:
                print(f"{self.agent.jid}: Waiting for a message.")    
    async def setup(self):
        print(f"Agent {self.jid} starting.")
        behaviour_availability = self.AvailabilityBehaviour()
        self.add_behaviour(behaviour_availability)
